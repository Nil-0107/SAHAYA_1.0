"""Role-scoped support request and assignment tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.database import get_db
from app.demo.personas import DEMO_PERSONAS
from app.demo.seed_demo import seed_demo
from app.main import app
from app.models.case import Case, CaseStatus
from app.models.case_assignment import AssignmentStatus, AssignmentType, CaseAssignment
from app.models.support_action import SupportAction, SupportActionStatus
from app.models.support_request import SupportRequest, SupportRequestStatus, SupportRequestType
from app.models.user import Role, User, UserStatus


PASSWORD = "ValidPass!123"


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    monkeypatch.setenv("SAATHI_ENV", "test")
    monkeypatch.setenv("SAATHI_DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    active_session = sessionmaker(bind=engine, expire_on_commit=False)()

    def override_database() -> Generator[Session, None, None]:
        yield active_session

    app.dependency_overrides[get_db] = override_database
    yield active_session
    app.dependency_overrides.clear()
    active_session.close()
    engine.dispose()


@pytest.fixture
def client(database: Session) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def _user(database: Session, suffix: str, role: Role = Role.VICTIM) -> User:
    user = User(
        phone=f"+9192000{suffix}",
        email=f"{suffix}@example.invalid",
        password_hash=hash_password(PASSWORD),
        role=role,
        status=UserStatus.ACTIVE,
        phone_verified_at=datetime.now(timezone.utc),
        profile_completed=True,
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    return user


def _case(database: Session, owner: User, number: str) -> Case:
    case = Case(
        owner_user_id=owner.id,
        case_number=number,
        category="synthetic",
        category_verified=False,
        status=CaseStatus.OPEN,
        stage="intake",
    )
    database.add(case)
    database.commit()
    database.refresh(case)
    return case


def _token(client: TestClient, user: User) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_victim_creates_and_reads_own_request_without_staff_fields(
    client: TestClient,
    database: Session,
) -> None:
    victim = _user(database, "1001")
    case = _case(database, victim, "SA-SUPPORT-1001")
    response = client.post(
        "/api/v1/support-requests",
        json={"case_id": case.id, "category": "counselling", "details": "I would like support follow-up."},
        headers=_headers(_token(client, victim)),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "counselling"
    assert body["status"] == "pending"
    assert body["is_demo"] is False
    assert body["assignments"] == []
    assert body["updates"] == []
    request = database.scalar(select(SupportRequest))
    assert request.user_id == victim.id
    assert request.case_id == case.id
    assert request.type == SupportRequestType.WELLBEING
    assert request.status == SupportRequestStatus.PENDING

    forbidden_fields = client.post(
        "/api/v1/support-requests",
        json={
            "case_id": case.id,
            "category": "legal_help",
            "details": "No staff fields",
            "assignee_user_id": 99,
            "status": "assigned",
            "user_id": 99,
        },
        headers=_headers(_token(client, victim)),
    )
    assert forbidden_fields.status_code == 422
    assert forbidden_fields.json()["error"]["code"] == "VALIDATION_ERROR"


def test_victim_cannot_read_another_victims_request(
    client: TestClient,
    database: Session,
) -> None:
    owner = _user(database, "1002")
    other = _user(database, "1003")
    case = _case(database, owner, "SA-SUPPORT-1002")
    created = client.post(
        "/api/v1/support-requests",
        json={"case_id": case.id, "category": "legal_help", "details": "Legal support request."},
        headers=_headers(_token(client, owner)),
    ).json()

    mine = client.get("/api/v1/support-requests/me", headers=_headers(_token(client, other)))
    assert mine.status_code == 200
    assert mine.json() == []
    detail = client.get(
        f"/api/v1/support-requests/{created['id']}",
        headers=_headers(_token(client, other)),
    )
    assert detail.status_code == 404
    assert detail.json()["error"]["code"] == "SUPPORT_REQUEST_NOT_FOUND"


def test_counsellor_and_district_officer_only_see_assigned_requests(
    client: TestClient,
    database: Session,
) -> None:
    victim = _user(database, "1004")
    counsellor = _user(database, "1005", Role.COUNSELLOR)
    district = _user(database, "1006", Role.DISTRICT_OFFICER)
    case = _case(database, victim, "SA-SUPPORT-1004")
    request = SupportRequest(
        user_id=victim.id,
        case_id=case.id,
        type=SupportRequestType.WELLBEING,
        status=SupportRequestStatus.ASSIGNED,
        priority="standard",
        explicit_human_request=True,
        details="Assigned support request.",
    )
    database.add(request)
    database.flush()
    assignment = CaseAssignment(
        case_id=case.id,
        support_request_id=request.id,
        assignee_user_id=counsellor.id,
        assigned_by_user_id=counsellor.id,
        assignment_type=AssignmentType.WELLBEING_COUNSELLOR,
        status=AssignmentStatus.ACTIVE,
        reason="Authorised synthetic assignment.",
        active=True,
    )
    database.add(assignment)
    database.commit()
    database.refresh(request)

    counsellor_response = client.get(
        "/api/v1/support-requests/me",
        headers=_headers(_token(client, counsellor)),
    )
    assert counsellor_response.status_code == 200
    assert [item["id"] for item in counsellor_response.json()] == [request.id]
    district_response = client.get(
        "/api/v1/support-requests/me",
        headers=_headers(_token(client, district)),
    )
    assert district_response.status_code == 200
    assert district_response.json() == []
    detail = client.get(
        f"/api/v1/support-requests/{request.id}",
        headers=_headers(_token(client, counsellor)),
    )
    assert detail.status_code == 200
    assert detail.json()["assignments"][0]["active"] is True


def test_support_updates_are_returned_to_authorized_owner(
    client: TestClient,
    database: Session,
) -> None:
    victim = _user(database, "1007")
    case = _case(database, victim, "SA-SUPPORT-1007")
    request = SupportRequest(
        user_id=victim.id,
        case_id=case.id,
        type=SupportRequestType.LEGAL,
        status=SupportRequestStatus.IN_PROGRESS,
        priority="standard",
        explicit_human_request=True,
        details="Support details.",
    )
    database.add(request)
    database.flush()
    database.add(
        SupportAction(
            support_request_id=request.id,
            actor_user_id=victim.id,
            action="request_created",
            status=SupportActionStatus.RECORDED,
            notes="Request received.",
        )
    )
    database.commit()
    response = client.get(
        f"/api/v1/support-requests/{request.id}",
        headers=_headers(_token(client, victim)),
    )
    assert response.status_code == 200
    assert response.json()["updates"][0]["notes"] == "Request received."


def test_demo_support_requests_are_real_seeded_data(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    victim = next(item for item in DEMO_PERSONAS if item.key == "user:victim:aarohi-demo")
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": victim.email, "password": victim.password},
    )
    assert login.status_code == 200
    response = client.get(
        "/api/v1/support-requests/me",
        headers=_headers(login.json()["access_token"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert all(item["is_demo"] is True for item in body)
    assert {item["category"] for item in body} == {"counselling", "legal_help", "protection_relocation"}
    assert all(item["updates"] for item in body)

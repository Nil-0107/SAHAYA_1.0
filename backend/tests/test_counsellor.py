"""Counsellor assignment-scoped dashboard tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.database import get_db
from app.demo.personas import DEMO_PERSONAS
from app.demo.seed_demo import seed_demo
from app.main import app
from app.models.case import Case, CaseStatus
from app.models.case_assignment import AssignmentType, CaseAssignment
from app.models.support_request import SupportRequest, SupportRequestType
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


def _user(database: Session, suffix: str, role: Role) -> User:
    user = User(
        phone=f"+9194000{suffix}",
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


def _token(client: TestClient, user: User) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_counsellor_dashboard_is_limited_to_active_assignments(
    client: TestClient,
    database: Session,
) -> None:
    counsellor = _user(database, "2001", Role.COUNSELLOR)
    owner = _user(database, "2002", Role.VICTIM)
    assigned_case = Case(
        owner_user_id=owner.id,
        case_number="SA-COUNSELLOR-ASSIGNED",
        category="synthetic",
        category_verified=False,
        status=CaseStatus.OPEN,
        stage="support",
    )
    unrelated_case = Case(
        owner_user_id=owner.id,
        case_number="SA-COUNSELLOR-UNRELATED",
        category="synthetic",
        category_verified=False,
        status=CaseStatus.OPEN,
        stage="intake",
    )
    database.add_all([assigned_case, unrelated_case])
    database.flush()
    assigned_request = SupportRequest(
        user_id=owner.id,
        case_id=assigned_case.id,
        type=SupportRequestType.WELLBEING,
        status="assigned",
        priority="normal",
        explicit_human_request=True,
        details="Synthetic assigned wellbeing request.",
    )
    unrelated_request = SupportRequest(
        user_id=owner.id,
        case_id=unrelated_case.id,
        type=SupportRequestType.WELLBEING,
        status="assigned",
        priority="normal",
        explicit_human_request=True,
        details="Must not be visible to this counsellor.",
    )
    database.add_all([assigned_request, unrelated_request])
    database.flush()
    database.add(
        CaseAssignment(
            case_id=assigned_case.id,
            support_request_id=assigned_request.id,
            assignee_user_id=counsellor.id,
            assigned_by_user_id=counsellor.id,
            assignment_type=AssignmentType.WELLBEING_COUNSELLOR,
            status="active",
            reason="Synthetic authorised counsellor assignment.",
            active=True,
        )
    )
    database.commit()

    response = client.get("/api/v1/counsellor/dashboard", headers=_headers(_token(client, counsellor)))
    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["support_requests"]] == [assigned_request.id]
    assert body["aggregate"]["assigned_request_count"] == 1
    assert all(item["id"] != unrelated_case.id for item in body["support_requests"])
    assert all(item["id"] != unrelated_request.id for item in body["support_requests"])


def test_counsellor_dashboard_rejects_other_role(
    client: TestClient,
    database: Session,
) -> None:
    victim = _user(database, "2003", Role.VICTIM)
    response = client.get(
        "/api/v1/counsellor/dashboard",
        headers=_headers(_token(client, victim)),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ROLE_FORBIDDEN"


def test_demo_counsellor_has_seeded_records(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    persona = next(item for item in DEMO_PERSONAS if item.key == "user:counsellor:leela-demo")
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": persona.email, "password": persona.password},
    )
    assert login.status_code == 200
    response = client.get(
        "/api/v1/counsellor/dashboard",
        headers=_headers(login.json()["access_token"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["aggregate"]["assigned_request_count"] == 2
    assert len(body["support_requests"]) == 2
    assert len(body["support_actions"]) == 3
    assert len(body["follow_ups"]) == 3
    assert body["notifications"]
    assert all(item["is_demo"] is True for item in body["support_requests"])
    assert all(item["is_demo"] is True for item in body["support_actions"])
    assert all(item["is_demo"] is True for item in body["notifications"])

"""Administrator aggregate dashboard tests."""

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


def test_non_admin_role_cannot_access_admin_dashboard(
    client: TestClient,
    database: Session,
) -> None:
    counsellor = _user(database, "3001", Role.COUNSELLOR)
    response = client.get(
        "/api/v1/admin/dashboard",
        headers=_headers(_token(client, counsellor)),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ROLE_FORBIDDEN"


def test_demo_admin_dashboard_is_aggregate_and_database_backed(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    persona = next(item for item in DEMO_PERSONAS if item.key == "user:admin:state-asha-demo")
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": persona.email, "password": persona.password},
    )
    assert login.status_code == 200
    response = client.get(
        "/api/v1/admin/dashboard?include_demo=true",
        headers=_headers(login.json()["access_token"]),
    )
    assert response.status_code == 200
    body = response.json()

    assert body["aggregate"]["total_case_count"] == 4
    assert body["aggregate"]["active_case_count"] == 4
    assert body["aggregate"]["total_support_request_count"] == 5
    assert body["aggregate"]["open_support_request_count"] == 5
    assert body["aggregate"]["resolved_support_request_count"] == 0
    assert body["aggregate"]["active_assignment_count"] == 5
    assert body["aggregate"]["district_count"] == 1
    assert body["aggregate"]["total_checkin_count"] == 4
    assert body["aggregate"]["total_user_count"] == 5
    assert body["aggregate"]["active_user_count"] == 5
    assert len(body["district_analytics"]) == 1
    assert body["district_analytics"][0]["district"] == "Demo District / Demo City"
    assert body["district_analytics"][0]["is_demo"] is True
    assert sum(item["count"] for item in body["support_request_counts"]["by_type"]) == 5
    assert sum(item["count"] for item in body["support_request_counts"]["by_status"]) == 5
    assert len(body["priority_queue"]) == 4
    assert {item["priority"] for item in body["priority_queue"]} == {"HIGH", "STANDARD", "REVIEW"}
    assert len(body["escalation_trends"]) == 1
    assert body["notifications"]
    assert all(item["is_demo"] is True for item in body["notifications"])

    headers = _headers(login.json()["access_token"])
    queue = client.get("/api/v1/admin/queue?include_demo=true", headers=headers)
    assert queue.status_code == 200
    assert {item["priority"] for item in queue.json()} == {"HIGH", "STANDARD", "REVIEW"}
    assert all("internal_score" not in item for item in queue.json())
    high_case = next(item for item in queue.json() if item["priority"] == "HIGH")
    recalculated = client.post(
        f"/api/v1/admin/cases/{high_case['case_id']}/priority-recalculate?include_demo=true",
        headers=headers,
    )
    assert recalculated.status_code == 200
    assert recalculated.json()["priority"] == "HIGH"
    assert recalculated.json()["explanation"]

    response_text = response.text.casefold()
    assert "aarohi" not in response_text
    assert "meher" not in response_text
    assert "@example.invalid" not in response_text
    assert "synthetic demo request:" not in response_text


def test_admin_dashboard_uses_current_database_counts(
    client: TestClient,
    database: Session,
) -> None:
    admin = _user(database, "3002", Role.ADMIN)
    response = client.get("/api/v1/admin/dashboard", headers=_headers(_token(client, admin)))
    assert response.status_code == 200
    body = response.json()
    assert body["aggregate"]["total_case_count"] == 0
    assert body["aggregate"]["total_support_request_count"] == 0
    assert body["district_analytics"] == []
    assert body["support_request_counts"] == {"by_type": [], "by_status": []}
    assert body["priority_queue"] == []
    assert body["escalation_trends"] == []
    assert body["notifications"] == []

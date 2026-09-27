"""Notification ownership, read-state, and demo-data tests."""

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
from app.models.notification import Notification
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


def _user(database: Session, suffix: str) -> User:
    user = User(
        phone=f"+9193000{suffix}",
        email=f"{suffix}@example.invalid",
        password_hash=hash_password(PASSWORD),
        role=Role.VICTIM,
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


def test_notifications_are_owner_scoped_and_read_state_is_persisted(
    client: TestClient,
    database: Session,
) -> None:
    owner = _user(database, "1001")
    other = _user(database, "1002")
    notification = Notification(
        user_id=owner.id,
        type="support_workflow",
        title="Support update",
        message="Synthetic notification.",
        is_read=False,
    )
    database.add(notification)
    database.commit()
    database.refresh(notification)

    mine = client.get("/api/v1/notifications", headers=_headers(_token(client, owner)))
    assert mine.status_code == 200
    assert len(mine.json()) == 1
    assert mine.json()[0]["is_read"] is False
    assert "user_id" not in mine.json()[0]

    marked = client.post(
        f"/api/v1/notifications/{notification.id}/read",
        headers=_headers(_token(client, owner)),
    )
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True
    assert marked.json()["read_at"] is not None
    database.refresh(notification)
    assert notification.is_read is True

    forbidden = client.post(
        f"/api/v1/notifications/{notification.id}/read",
        headers=_headers(_token(client, other)),
    )
    assert forbidden.status_code == 404
    assert forbidden.json()["error"]["code"] == "NOTIFICATION_NOT_FOUND"
    assert client.get("/api/v1/notifications", headers=_headers(_token(client, other))).json() == []


def test_read_all_marks_only_authenticated_users_notifications(
    client: TestClient,
    database: Session,
) -> None:
    owner = _user(database, "1003")
    other = _user(database, "1004")
    database.add_all([
        Notification(user_id=owner.id, type="case_update", title="One", message="One", is_read=False),
        Notification(user_id=owner.id, type="support_update", title="Two", message="Two", is_read=False),
        Notification(user_id=other.id, type="case_update", title="Other", message="Other", is_read=False),
    ])
    database.commit()

    response = client.post("/api/v1/notifications/read-all", headers=_headers(_token(client, owner)))
    assert response.status_code == 200
    assert response.json()["updated_count"] == 2
    assert all(item.is_read for item in database.scalars(select(Notification).where(Notification.user_id == owner.id)).all())
    assert database.scalar(select(Notification).where(Notification.user_id == other.id, Notification.is_read.is_(False))) is not None


def test_every_demo_persona_has_real_fictional_notifications(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    for persona in DEMO_PERSONAS:
        login = client.post(
            "/api/v1/auth/login",
            json={"identifier": persona.email, "password": persona.password},
        )
        assert login.status_code == 200
        response = client.get(
            "/api/v1/notifications",
            headers=_headers(login.json()["access_token"]),
        )
        assert response.status_code == 200, persona.email
        body = response.json()
        assert body, persona.email
        assert all(item["is_demo"] is True for item in body)
        assert all(item["title"] and item["message"] for item in body)

def test_authorised_staff_can_open_notification_target_details(client: TestClient, database: Session) -> None:
    seed_demo(database)
    persona = next(item for item in DEMO_PERSONAS if item.key == "user:admin:state-asha-demo")
    login = client.post("/api/v1/auth/login", json={"identifier": persona.email, "password": persona.password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    notes = client.get("/api/v1/notifications", headers=_headers(token))
    assert notes.status_code == 200
    linked = next(item for item in notes.json() if item["case_id"] is not None)
    detail = client.get(f"/api/v1/notifications/{linked['id']}/target-details", headers=_headers(token))
    assert detail.status_code == 200
    body = detail.json()
    assert body["user"]["full_name"]
    assert body["case"]["case_number"]

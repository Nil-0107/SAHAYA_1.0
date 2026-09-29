"""Ownership, persistence, inference, and demo-history check-in tests."""

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
from app.ml.inference import MLPrediction, MLPredictionError
from app.models.checkin import Checkin, CheckinAnalysisStatus
from app.models.user import Role, User, UserStatus


PASSWORD = "ValidPass!123"


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    monkeypatch.setenv("SAHAYA_ENV", "test")
    monkeypatch.setenv("SAHAYA_DATABASE_URL", "sqlite:///:memory:")
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


def _user(
    database: Session,
    *,
    suffix: str,
    verified: bool = True,
    profile_complete: bool = True,
) -> User:
    user = User(
        phone=f"+9190000{suffix}",
        email=f"{suffix}@example.invalid",
        password_hash=hash_password(PASSWORD),
        role=Role.VICTIM,
        status=UserStatus.ACTIVE,
        phone_verified_at=datetime.now(timezone.utc) if verified else None,
        profile_completed=profile_complete,
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    return user


def _login(client: TestClient, user: User) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_checkin_persists_real_ml_result(
    database: Session,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _user(database, suffix="0001")
    monkeypatch.setattr(
        "app.services.checkin_service.MLService.predict",
        lambda self, text: MLPrediction(
            class_id=3,
            label=None,
            confidence=0.72,
            model_version="logistic_regression_emotion_model.joblib",
        ),
    )
    token = _login(client, user)

    response = client.post(
        "/api/v1/checkins",
        json={"text": "  I am reflecting on today.  "},
        headers=_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "I am reflecting on today."
    assert body["class_id"] == 3
    assert body["label"] is None
    assert body["confidence"] == pytest.approx(0.72)
    assert body["model_version"] == "logistic_regression_emotion_model.joblib"
    assert body["analysis_status"] == "completed"
    record = database.scalar(select(Checkin))
    assert record.user_id == user.id
    assert record.analysis_status == CheckinAnalysisStatus.COMPLETED
    assert record.predicted_class == 3
    assert record.predicted_label is None


def test_list_and_get_are_scoped_to_authenticated_user(
    database: Session,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = _user(database, suffix="0002")
    other = _user(database, suffix="0003")
    monkeypatch.setattr(
        "app.services.checkin_service.MLService.predict",
        lambda self, text: MLPrediction(1, None, None, "test-model"),
    )
    owner_token = _login(client, owner)
    other_token = _login(client, other)
    created = client.post(
        "/api/v1/checkins",
        json={"text": "Owner check-in"},
        headers=_headers(owner_token),
    ).json()

    mine = client.get("/api/v1/checkins/me", headers=_headers(owner_token))
    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()] == [created["id"]]

    fetched = client.get(
        f"/api/v1/checkins/{created['id']}",
        headers=_headers(owner_token),
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]

    forbidden_lookup = client.get(
        f"/api/v1/checkins/{created['id']}",
        headers=_headers(other_token),
    )
    assert forbidden_lookup.status_code == 404
    assert forbidden_lookup.json()["error"]["code"] == "CHECKIN_NOT_FOUND"
    assert other_token not in forbidden_lookup.text


def test_unverified_and_incomplete_users_cannot_create_checkins(
    database: Session,
    client: TestClient,
) -> None:
    unverified = _user(database, suffix="0004", verified=False, profile_complete=False)
    incomplete = _user(database, suffix="0005", verified=True, profile_complete=False)
    for user, code in (
        (unverified, "ACCOUNT_MOBILE_NOT_VERIFIED"),
        (incomplete, "PROFILE_INCOMPLETE"),
    ):
        response = client.post(
            "/api/v1/checkins",
            json={"text": "hello"},
            headers=_headers(_login(client, user)),
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == code


def test_empty_checkin_is_rejected(client: TestClient, database: Session) -> None:
    user = _user(database, suffix="0006")
    response = client.post(
        "/api/v1/checkins",
        json={"text": "   "},
        headers=_headers(_login(client, user)),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_case_id_must_belong_to_authenticated_user(
    database: Session,
    client: TestClient,
) -> None:
    from app.models.case import Case

    owner = _user(database, suffix="0007")
    other = _user(database, suffix="0008")
    case = Case(
        owner_user_id=other.id,
        case_number="SA-CHECKIN-OTHER",
        category="synthetic",
        category_verified=False,
        stage="intake",
    )
    database.add(case)
    database.commit()

    response = client.post(
        "/api/v1/checkins",
        json={"text": "hello", "case_id": case.id},
        headers=_headers(_login(client, owner)),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CASE_NOT_FOUND"


def test_ml_failure_returns_safe_error(
    database: Session,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _user(database, suffix="0009")

    def fail(self, text: str):
        raise MLPredictionError("internal model details")

    monkeypatch.setattr("app.services.checkin_service.MLService.predict", fail)
    response = client.post(
        "/api/v1/checkins",
        json={"text": "hello"},
        headers=_headers(_login(client, user)),
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "CHECKIN_ANALYSIS_UNAVAILABLE"
    assert "internal model details" not in response.text


def test_demo_victim_history_is_real_database_data(
    database: Session,
    client: TestClient,
) -> None:
    seed_demo(database)
    persona = next(item for item in DEMO_PERSONAS if item.key == "user:victim:aarohi-demo")
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": persona.email, "password": persona.password},
    )
    assert login.status_code == 200
    response = client.get(
        "/api/v1/checkins/me",
        headers=_headers(login.json()["access_token"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert all(item["class_id"] is None for item in body)
    assert all(item["label"] is None for item in body)
    assert all(item["confidence"] is None for item in body)
    assert all(item["created_at"] for item in body)

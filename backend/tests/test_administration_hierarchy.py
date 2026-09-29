"""Hierarchical administrative provisioning and geographic-scope tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.database import get_db
from app.demo.personas import DEMO_PERSONAS
from app.demo.seed_demo import seed_demo
from app.main import app
from app.models.administrative_unit import AdministrativeUnit
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.support_request import SupportRequest
from app.models.user import Role, User


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


def _login(client: TestClient, key: str) -> dict[str, str]:
    persona = next(item for item in DEMO_PERSONAS if item.key == key)
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": persona.email, "password": persona.password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "full_name": "Provisioned Test User",
        "display_name": "Provisioned User",
        "email": "provisioned@example.invalid",
        "phone": "9876500011",
        "password": "Provisioned!2026",
        "language": "English",
    }
    payload.update(overrides)
    return payload


def test_national_creates_state_then_state_creates_district_then_district_appoints_counsellor(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    national_headers = _login(client, "user:admin:national-rohan-demo")

    state_response = client.post(
        "/api/v1/admin/state-administrators",
        headers=national_headers,
        json=_payload(email="new.state@example.invalid", phone="9876500011", state_name="New Demo State"),
    )
    assert state_response.status_code == 201, state_response.text
    state_body = state_response.json()
    assert state_body["role"] == "state_admin"
    assert state_body["created_by_user_id"] is not None

    state_id = state_body["state_id"]
    state_user = database.get(User, state_body["id"])
    assert state_user is not None
    state_headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'identifier': state_user.email, 'password': 'Provisioned!2026'}).json()['access_token']}"}
    district_response = client.post(
        "/api/v1/admin/district-administrators",
        headers=state_headers,
        json=_payload(
            email="new.district@example.invalid",
            phone="9876500012",
            state_id=state_id,
            district_name="New Demo District",
        ),
    )
    assert district_response.status_code == 201, district_response.text
    district_body = district_response.json()
    assert district_body["role"] == "district_admin"
    assert district_body["state_id"] == state_id

    district_user = database.get(User, district_body["id"])
    assert district_user is not None
    district_headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'identifier': district_user.email, 'password': 'Provisioned!2026'}).json()['access_token']}"}
    counsellor_response = client.post(
        "/api/v1/admin/counsellors",
        headers=district_headers,
        json=_payload(
            email="new.counsellor@example.invalid",
            phone="9876500013",
            district_id=district_body["district_id"],
        ),
    )
    assert counsellor_response.status_code == 201, counsellor_response.text
    counsellor_body = counsellor_response.json()
    assert counsellor_body["role"] == "counsellor"
    assert counsellor_body["appointed_by_user_id"] == district_body["id"]

    notifications = database.scalars(
        select(Notification).where(Notification.user_id == counsellor_body["id"])
    ).all()
    assert notifications
    assert "appointed" in notifications[0].message.casefold()
    audits = database.scalars(
        select(AuditLog).where(AuditLog.resource_id == str(counsellor_body["id"]))
    ).all()
    assert any(item.action == "COUNSELLOR_APPOINTED" for item in audits)


def test_geographic_scope_rejects_cross_state_and_cross_district_creation(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    national_headers = _login(client, "user:admin:national-rohan-demo")
    other_state = client.post(
        "/api/v1/admin/state-administrators",
        headers=national_headers,
        json=_payload(email="other.state@example.invalid", phone="9876500021", state_name="Other State"),
    ).json()
    state_headers = _login(client, "user:admin:state-asha-demo")
    cross_state = client.post(
        "/api/v1/admin/district-administrators",
        headers=state_headers,
        json=_payload(
            email="cross.state@example.invalid",
            phone="9876500022",
            state_id=other_state["state_id"],
            district_name="Wrong District",
        ),
    )
    assert cross_state.status_code == 403
    assert cross_state.json()["error"]["code"] == "GEOGRAPHIC_SCOPE_FORBIDDEN"

    district_headers = _login(client, "user:district:kabir-demo")
    other_district = database.scalar(
        select(AdministrativeUnit).where(
            AdministrativeUnit.unit_type == "district",
            AdministrativeUnit.name == "Other District",
        )
    )
    if other_district is None:
        other_district = AdministrativeUnit(name="Other District", unit_type="district")
        database.add(other_district)
        database.commit()
    cross_district = client.post(
        "/api/v1/admin/counsellors",
        headers=district_headers,
        json=_payload(email="cross.district@example.invalid", phone="9876500023", district_id=other_district.id),
    )
    assert cross_district.status_code == 403
    assert cross_district.json()["error"]["code"] == "GEOGRAPHIC_SCOPE_FORBIDDEN"


def test_unprivileged_roles_cannot_create_administrative_accounts(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    victim_headers = _login(client, "user:victim:aarohi-demo")
    counsellor_headers = _login(client, "user:counsellor:leela-demo")
    for headers, path in (
        (victim_headers, "/api/v1/admin/state-administrators"),
        (counsellor_headers, "/api/v1/admin/counsellors"),
    ):
        response = client.post(path, headers=headers, json=_payload())
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "ROLE_FORBIDDEN"


def test_assignment_and_support_action_complete_the_authorised_workflow(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    victim_headers = _login(client, "user:victim:meher-demo")
    case_id = client.get("/api/v1/cases/me", headers=victim_headers).json()[0]["id"]
    created = client.post(
        "/api/v1/support-requests",
        headers=victim_headers,
        json={"case_id": case_id, "category": "counselling", "details": "New authorised follow-up request."},
    )
    assert created.status_code == 201
    request_id = created.json()["id"]

    district_headers = _login(client, "user:district:kabir-demo")
    counsellor = database.scalar(select(User).where(User.email == "leela.counsellor.demo@example.invalid"))
    assert counsellor is not None
    assignment = client.post(
        "/api/v1/case-assignments",
        headers=district_headers,
        json={
            "support_request_id": request_id,
            "assignee_user_id": counsellor.id,
            "assignment_type": "wellbeing_counsellor",
            "reason": "Authorised synthetic follow-up assignment.",
        },
    )
    assert assignment.status_code == 201, assignment.text
    assert assignment.json()["active"] is True

    counsellor_headers = _login(client, "user:counsellor:leela-demo")
    action = client.post(
        f"/api/v1/support-requests/{request_id}/actions",
        headers=counsellor_headers,
        json={"action": "follow_up", "notes": "Synthetic follow-up recorded.", "request_status": "in_progress"},
    )
    assert action.status_code == 201, action.text
    detail = client.get(f"/api/v1/support-requests/{request_id}", headers=victim_headers)
    assert detail.status_code == 200
    assert detail.json()["status"] == "in_progress"
    assert any(item["action"] == "follow_up" for item in detail.json()["updates"])


def test_administrator_cannot_use_generic_support_endpoint_for_raw_victim_content(
    client: TestClient,
    database: Session,
) -> None:
    seed_demo(database)
    headers = _login(client, "user:admin:national-rohan-demo")
    listed = client.get("/api/v1/support-requests/me", headers=headers)
    assert listed.status_code == 200
    assert listed.json() == []
    request = database.scalar(select(SupportRequest))
    assert request is not None
    request_id = request.id
    detail = client.get(f"/api/v1/support-requests/{request_id}", headers=headers)
    assert detail.status_code == 404
    assert detail.json()["error"]["code"] == "SUPPORT_REQUEST_NOT_FOUND"

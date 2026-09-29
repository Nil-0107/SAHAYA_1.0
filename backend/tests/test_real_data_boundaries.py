"""Regression tests for test-auth isolation and real legal-help routing."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.database import get_db
from app.demo.personas import DEMO_PERSONAS
from app.demo.seed_demo import seed_demo
from app.demo.seed_test_auth import seed_local_test_accounts
from app.main import app
from app.models import AdministrativeUnit, Case, Notification, Role, SupportRequest, User, UserStatus


PASSWORD = "ValidPass!123"


def _database() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"identifier": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_local_test_auth_seed_has_no_application_records(monkeypatch) -> None:
    monkeypatch.setenv("SAHAYA_ENV", "test")
    database = _database()
    app.dependency_overrides[get_db] = lambda: database
    try:
        seed_local_test_accounts(database)
        with TestClient(app) as client:
            for persona in DEMO_PERSONAS:
                if persona.key == "user:victim:meher-demo":
                    continue
                response = client.post(
                    "/api/v1/auth/login",
                    json={"identifier": persona.email, "password": persona.password},
                )
                assert response.status_code == 200, persona.email
                assert response.json()["user"]["role"] == persona.role.value
        assert database.scalar(select(Case.id)) is None
        assert database.scalar(select(SupportRequest.id)) is None
        assert database.scalar(select(Notification.id)) is None
    finally:
        app.dependency_overrides.clear()
        database.close()


def test_normal_apis_hide_demo_application_data(monkeypatch) -> None:
    monkeypatch.setenv("SAHAYA_ENV", "test")
    monkeypatch.setenv("SAHAYA_INCLUDE_DEMO_DATA", "false")
    database = _database()
    app.dependency_overrides[get_db] = lambda: database
    try:
        seed_demo(database)
        persona = next(item for item in DEMO_PERSONAS if item.key == "user:victim:aarohi-demo")
        with TestClient(app) as client:
            headers = _headers(client, persona.email, persona.password)
            assert client.get("/api/v1/cases/me", headers=headers).json() == []
            assert client.get("/api/v1/checkins/me", headers=headers).json() == []
            assert client.get("/api/v1/support-requests/me", headers=headers).json() == []
            assert client.get("/api/v1/notifications", headers=headers).json() == []
    finally:
        app.dependency_overrides.clear()
        database.close()


def test_real_legal_request_routes_to_correct_district_and_is_actionable(monkeypatch) -> None:
    monkeypatch.setenv("SAHAYA_ENV", "test")
    monkeypatch.setenv("SAHAYA_INCLUDE_DEMO_DATA", "false")
    database = _database()
    state_a = AdministrativeUnit(name="State A", unit_type="state")
    district_a = AdministrativeUnit(name="District A", unit_type="district", parent=state_a)
    state_b = AdministrativeUnit(name="State B", unit_type="state")
    district_b = AdministrativeUnit(name="District B", unit_type="district", parent=state_b)
    database.add_all([state_a, district_a, state_b, district_b])
    database.flush()

    def user(email: str, role: Role, district: AdministrativeUnit, state: AdministrativeUnit) -> User:
        account = User(
            email=email,
            phone=f"+919{len(email)}{abs(hash(email)) % 100000:05d}",
            password_hash=hash_password(PASSWORD),
            role=role,
            status=UserStatus.ACTIVE,
            phone_verified_at=datetime.now(timezone.utc),
            profile_completed=True,
            state_id=state.id,
            district_id=district.id,
        )
        database.add(account)
        database.flush()
        return account

    victim = user("victim-real@example.invalid", Role.VICTIM, district_a, state_a)
    district_admin = user("district-a@example.invalid", Role.DISTRICT_ADMIN, district_a, state_a)
    other_admin = user("district-b@example.invalid", Role.DISTRICT_ADMIN, district_b, state_b)
    case = Case(owner_user_id=victim.id, case_number="SA-REAL-LEGAL-1", category="general_support", status="open", stage="intake")
    database.add(case)
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        with TestClient(app) as client:
            victim_headers = _headers(client, victim.email, PASSWORD)
            created = client.post(
                "/api/v1/support-requests",
                json={"case_id": case.id, "category": "legal_help", "details": "I need authorised legal assistance."},
                headers=victim_headers,
            )
            assert created.status_code == 201, created.text
            request = created.json()
            assert request["category"] == "legal_help"
            assert request["status"] == "assigned"
            assert database.scalar(select(SupportRequest).where(SupportRequest.id == request["id"])) is not None

            district_headers = _headers(client, district_admin.email, PASSWORD)
            dashboard = client.get("/api/v1/district/dashboard", headers=district_headers)
            assert dashboard.status_code == 200
            assert [item["id"] for item in dashboard.json()["assistance_requests"]] == [request["id"]]
            assert client.post(
                f"/api/v1/support-requests/{request['id']}/actions",
                json={"action": "review_started", "notes": "District review started.", "request_status": "in_progress"},
                headers=district_headers,
            ).status_code == 201

            wrong_headers = _headers(client, other_admin.email, PASSWORD)
            assert client.get("/api/v1/support-requests/me", headers=wrong_headers).json() == []
            assert client.post(
                f"/api/v1/support-requests/{request['id']}/actions",
                json={"action": "wrong_scope", "notes": "Should be rejected."},
                headers=wrong_headers,
            ).status_code == 403

            notification = database.scalar(select(Notification).where(Notification.user_id == district_admin.id))
            assert notification is not None
            assert notification.case_id == case.id
    finally:
        app.dependency_overrides.clear()
        database.close()

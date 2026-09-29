from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import pytest
from fastapi.testclient import TestClient

from app.main import app

from app.core.config import DemoSeedEnvironmentError
from app.core.security import verify_password
from app.db.base import Base
from app.db.database import get_db
from app.demo.personas import DEMO_PERSONAS
from app.models import (
    AuditLog,
    Case,
    CaseAssignment,
    CaseDocument,
    Checkin,
    DEMO_MANAGED_MODELS,
    Notification,
    Profile,
    Role,
    SupportAction,
    SupportRequest,
    User,
)
from app.demo.seed_demo import DemoSeedConflictError, seed_demo


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch) -> Session:
    monkeypatch.setenv("SAHAYA_ENV", "test")
    monkeypatch.setenv("SAHAYA_DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    active_session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield active_session
    active_session.close()
    engine.dispose()


def test_seed_has_no_public_api_route() -> None:
    paths = {
        route.path.casefold()
        for route in app.routes
        if isinstance(getattr(route, "path", None), str)
    }
    assert not any("seed" in path or "demo" in path for path in paths)


def test_seed_is_complete_idempotent_and_marked(database: Session) -> None:
    first = seed_demo(database)
    assert first.created == 66
    assert first.updated == 0

    second = seed_demo(database)
    assert second.created == 0
    assert second.updated == 0
    assert second.unchanged == 66

    users = database.scalars(select(User)).all()
    assert len(users) == 6
    assert {user.role for user in users} == set(Role)
    assert all(user.is_demo and user.demo_key for user in users)
    personas_by_email = {persona.email: persona for persona in DEMO_PERSONAS}
    assert len({persona.password for persona in DEMO_PERSONAS}) == len(DEMO_PERSONAS)
    assert all(
        verify_password(personas_by_email[user.email].password, user.password_hash)
        for user in users
    )
    assert all(user.profile and user.profile.is_demo for user in users)

    for model in DEMO_MANAGED_MODELS:
        rows = database.scalars(select(model)).all()
        assert rows, f"{model.__tablename__} should have demo records"
        assert all(row.is_demo is True for row in rows)
        assert all(row.demo_key for row in rows)

    assert database.scalar(select(Profile).where(Profile.emergency_contact_phone.is_not(None))) is not None
    assert database.scalar(select(Case).where(Case.protection_request_open.is_(True))) is not None


def test_support_assignment_and_notification_relationships(database: Session) -> None:
    seed_demo(database)

    requests = database.scalars(select(SupportRequest)).all()
    assignments = database.scalars(select(CaseAssignment)).all()
    assert len(requests) == 5
    assert len(assignments) == 5
    assert all(request.case_id and request.user_id for request in requests)
    assert all(assignment.case_id and assignment.support_request_id for assignment in assignments)
    assert {assignment.assignee_user_id for assignment in assignments} == {
        user.id for user in database.scalars(select(User)).all() if user.role in {
            Role.COUNSELLOR,
            Role.DISTRICT_OFFICER,
        }
    }

    notifications = database.scalars(select(Notification)).all()
    assert len(notifications) == 12
    assert all(notification.user_id and notification.case_id for notification in notifications)


def test_role_specific_demo_assets_are_present(database: Session) -> None:
    seed_demo(database)

    assert database.scalar(select(CaseDocument)) is not None
    assert len(database.scalars(select(Checkin)).all()) == 4
    assert len(database.scalars(select(SupportAction)).all()) == 7

    assignments = database.scalars(select(CaseAssignment)).all()
    assert len([item for item in assignments if item.assignment_type == "district_coordination"]) == 3
    assert len([item for item in assignments if item.assignment_type == "wellbeing_counsellor"]) == 2

    audit_rows = database.scalars(select(AuditLog)).all()
    actions = {row.action for row in audit_rows}
    assert "DEMO_CASE_TIMELINE" in actions
    assert "DEMO_PRIORITY_EXAMPLE" in actions
    assert "DEMO_ADMIN_AGGREGATE_SNAPSHOT" in actions
    aggregate = next(
        row for row in audit_rows if row.action == "DEMO_ADMIN_AGGREGATE_SNAPSHOT"
    )
    assert aggregate.metadata_json["active_demo_cases"] == 4
    assert aggregate.metadata_json["demo_support_requests"] == 5
    assert aggregate.metadata_json["contains_sensitive_victim_content"] is False


def test_every_demo_persona_authenticates_through_normal_login(database: Session) -> None:
    seed_demo(database)
    app.dependency_overrides[get_db] = lambda: database
    try:
        with TestClient(app) as client:
            for persona in DEMO_PERSONAS:
                response = client.post(
                    "/api/v1/auth/login",
                    json={"identifier": persona.email, "password": persona.password},
                )
                assert response.status_code == 200, persona.email
                body = response.json()
                assert body["user"]["email"] == persona.email
                assert body["user"]["role"] == persona.role.value
                assert body["user"]["is_demo"] is True
                assert body["user"]["status"] == "active"
                assert body["user"]["phone_verified_at"] is not None
                assert body["user"]["profile_completed"] is True
                duplicate_profile = client.post(
                    "/api/v1/profile",
                    headers={"Authorization": f"Bearer {body['access_token']}"},
                    json={
                        "full_name": "Should Not Replace",
                        "display_name": "Should Not Replace",
                        "preferred_language": "English",
                        "city_or_district": "Demo District",
                        "consent": True,
                    },
                )
                assert duplicate_profile.status_code == 409
                assert duplicate_profile.json()["error"]["code"] == "PROFILE_ALREADY_COMPLETED"
    finally:
        app.dependency_overrides.clear()


def test_seed_requires_explicit_environment(database: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAHAYA_ENV", raising=False)
    with pytest.raises(DemoSeedEnvironmentError, match="blocked"):
        seed_demo(database)
    assert database.scalar(select(User)) is None


def test_seed_refuses_production_environment(database: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAHAYA_ENV", "production")
    with pytest.raises(DemoSeedEnvironmentError, match="blocked"):
        seed_demo(database)
    assert database.scalar(select(User)) is None


def test_seed_refuses_production_looking_url(database: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAHAYA_ENV", "development")
    monkeypatch.setenv("SAHAYA_DATABASE_URL", "sqlite:///sahaya_production.db")
    with pytest.raises(DemoSeedEnvironmentError, match="production-looking"):
        seed_demo(database)
    assert database.scalar(select(User)) is None


def test_seed_refuses_to_overwrite_real_natural_key(database: Session) -> None:
    real_user = User(
        email="aarohi.demo@example.invalid",
        phone="9000000000",
        password_hash="real-account-hash-is-never-replaced",
        role=Role.VICTIM,
        profile_completed=True,
    )
    database.add(real_user)
    database.commit()

    with pytest.raises(DemoSeedConflictError, match="non-demo"):
        seed_demo(database)

    database.refresh(real_user)
    assert real_user.is_demo is False
    assert real_user.password_hash == "real-account-hash-is-never-replaced"
    assert database.scalar(select(Profile)) is None


def test_natural_key_conflict_rolls_back_all_prior_demo_writes(database: Session) -> None:
    real_user = User(
        email="real.person@example.invalid",
        phone="9000000000",
        password_hash="real-hash",
        role=Role.VICTIM,
    )
    database.add(real_user)
    database.flush()
    real_case = Case(
        owner_user_id=real_user.id,
        case_number="SA-DEMO-1001",
        category="real",
        category_verified=False,
        stage="real",
    )
    database.add(real_case)
    database.commit()

    with pytest.raises(DemoSeedConflictError, match="SA-DEMO-1001"):
        seed_demo(database)

    assert database.scalar(select(User.id).where(User.is_demo.is_(True))) is None
    database.refresh(real_case)
    assert real_case.is_demo is False

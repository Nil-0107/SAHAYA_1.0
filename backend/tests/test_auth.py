"""Real authentication endpoint, session, role, and account-status tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db, require_roles
from app.core.security import hash_password, verify_password
from app.db.base import Base
from app.main import app
from app.models.user import Role, User, UserStatus


PASSWORD = "ValidPass!123"


@pytest.fixture
def database() -> Generator[Session, None, None]:
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


def _signup(client: TestClient, *, phone: str = "9876543210", email: str | None = None):
    return client.post(
        "/api/v1/auth/signup",
        json={
            "phone": phone,
            "email": email,
            "password": PASSWORD,
            "date_of_birth": "2000-01-01",
            "role": "victim",
        },
    )


def _login(client: TestClient, identifier: str):
    return client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": PASSWORD},
    )


def _create_staff_user(
    database: Session,
    *,
    role: Role,
    suffix: str,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    user = User(
        phone=f"+919{suffix.zfill(9)}",
        email=f"{suffix}@example.invalid",
        password_hash=hash_password(PASSWORD),
        role=role,
        status=status,
        phone_verified_at=(
            datetime.now(timezone.utc)
            if status == UserStatus.ACTIVE
            else None
        ),
        profile_completed=True,
        is_active=status not in {UserStatus.SUSPENDED, UserStatus.DISABLED},
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    return user


def test_signup_login_me_and_refresh(database: Session, client: TestClient) -> None:
    signup = _signup(client, email="Victim@Example.INVALID")
    assert signup.status_code == 201
    signup_body = signup.json()
    assert signup_body["user"]["role"] == "victim"
    assert signup_body["user"]["status"] == "active"
    assert signup_body["verification_required"] is False
    assert signup_body["user"]["phone_verified_at"] is not None
    assert signup_body["user"]["is_demo"] is False

    stored_user = database.query(User).one()
    assert stored_user.password_hash != PASSWORD
    assert verify_password(PASSWORD, stored_user.password_hash)
    assert stored_user.password_hash.startswith("scrypt$v1$")
    assert hash_password(PASSWORD) != hash_password(PASSWORD)
    assert stored_user.is_demo is False

    login = _login(client, "9876543210")
    assert login.status_code == 200
    login_body = login.json()
    assert login_body["token_type"] == "bearer"
    assert login_body["user"]["phone"] == "+919876543210"
    assert "saathi_refresh" in client.cookies
    access_token = login_body["access_token"]

    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    assert me.json()["id"] == stored_user.id
    assert me.json()["role"] == "victim"

    # Login is smooth and does not ask for OTP. A fresh login rotates the session.
    second_login = _login(client, "victim@example.invalid")
    assert second_login.status_code == 200
    new_access_token = second_login.json()["access_token"]
    assert new_access_token != access_token

    refresh = client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 200
    refreshed_token = refresh.json()["access_token"]
    assert client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {refreshed_token}"}
    ).status_code == 200


def test_wrong_password_uses_generic_error(client: TestClient) -> None:
    _signup(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "9876543210", "password": "WrongPass!123"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert "identifier" not in response.text.casefold() or "9876543210" not in response.text


def test_duplicate_account_is_rejected(database: Session, client: TestClient) -> None:
    assert _signup(client, email="one@example.invalid").status_code == 201
    duplicate = _signup(client, email="two@example.invalid")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_ACCOUNT"
    duplicate_email = client.post(
        "/api/v1/auth/signup",
        json={
            "phone": "9876543211",
            "email": "one@example.invalid",
            "password": PASSWORD,
            "date_of_birth": "2000-01-01",
            "role": "victim",
        },
    )
    assert duplicate_email.status_code == 409
    assert database.query(User).count() == 1


def test_protected_route_and_invalid_token(client: TestClient) -> None:
    missing = client.get("/api/v1/me")
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    invalid = client.get(
        "/api/v1/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "INVALID_TOKEN"


def test_logout_revokes_access_and_clears_refresh_cookie(
    database: Session, client: TestClient
) -> None:
    _signup(client)
    access_token = _login(client, "9876543210").json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    assert client.get("/api/v1/me", headers=headers).status_code == 200

    logout = client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert logout.json() == {"message": "Logged out"}
    assert "saathi_refresh" not in client.cookies

    revoked = client.get("/api/v1/me", headers=headers)
    assert revoked.status_code == 401
    assert revoked.json()["error"]["code"] == "SESSION_REVOKED"


def test_all_roles_authenticate_and_role_dependency_enforces_scope(
    database: Session, client: TestClient
) -> None:
    role_app = FastAPI()
    role_app.dependency_overrides[get_db] = lambda: database

    for role in Role:
        @role_app.get(f"/_test/{role.value}")
        def protected(
            user: User = Depends(require_roles(role)),
        ) -> dict[str, str]:
            return {"role": user.role.value}

    with TestClient(role_app) as role_client:
        for index, role in enumerate(Role, start=1):
            user = _create_staff_user(
                database,
                role=role,
                suffix=f"80000{index}",
            )
            login = _login(client, user.phone)
            assert login.status_code == 200
            assert login.json()["user"]["role"] == role.value
            token = login.json()["access_token"]
            authorized = role_client.get(
                f"/_test/{role.value}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert authorized.status_code == 200
            assert authorized.json()["role"] == role.value

            forbidden_role = next(candidate for candidate in Role if candidate != role)
            forbidden = role_client.get(
                f"/_test/{forbidden_role.value}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert forbidden.status_code == 403
            client.cookies.clear()


def test_protected_role_routes_require_verified_and_complete_accounts(
    database: Session, client: TestClient
) -> None:
    role_app = FastAPI()
    role_app.dependency_overrides[get_db] = lambda: database

    @role_app.get("/_test/protected")
    def protected(user: User = Depends(require_roles(Role.VICTIM))) -> dict[str, str]:
        return {"role": user.role.value}

    unverified = User(
        phone="+919000000001",
        email="unverified@example.invalid",
        password_hash=hash_password(PASSWORD),
        role=Role.VICTIM,
        status=UserStatus.ACTIVE,
        phone_verified_at=None,
        profile_completed=False,
    )
    incomplete = User(
        phone="+919000000002",
        email="incomplete@example.invalid",
        password_hash=hash_password(PASSWORD),
        role=Role.VICTIM,
        status=UserStatus.ACTIVE,
        phone_verified_at=datetime.now(timezone.utc),
        profile_completed=False,
    )
    database.add_all([unverified, incomplete])
    database.commit()

    with TestClient(role_app) as role_client:
        for user, expected_code in ((unverified, "ACCOUNT_MOBILE_NOT_VERIFIED"), (incomplete, "PROFILE_INCOMPLETE")):
            login = _login(client, user.phone)
            assert login.status_code == 200
            response = role_client.get(
                "/_test/protected",
                headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            )
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == expected_code


def test_public_signup_cannot_escalate_to_privileged_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "phone": "9876500000",
            "email": "escalation@example.invalid",
            "password": PASSWORD,
            "role": "admin",
        },
    )
    assert response.status_code == 422


def test_suspended_account_cannot_login(database: Session, client: TestClient) -> None:
    user = _create_staff_user(
        database,
        role=Role.COUNSELLOR,
        suffix="81000",
        status=UserStatus.SUSPENDED,
    )
    response = _login(client, user.phone)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_UNAVAILABLE"

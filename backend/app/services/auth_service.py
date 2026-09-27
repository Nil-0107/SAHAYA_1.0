"""Authentication, JWT, refresh-session, and account-status services."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import find_user_by_identifier, hash_password, verify_password
from app.models.audit_log import AuditLog
from app.models.user import Role, User, UserStatus


class AuthServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class IssuedSession:
    access_token: str
    refresh_token: str
    expires_in: int
    user: User


@dataclass(frozen=True, slots=True)
class DecodedToken:
    user_id: int
    role: Role
    session_version: int
    token_type: str


# Perform a real scrypt verification for unknown identifiers to reduce timing-based
# account enumeration. This is not a credential and is never persisted.
_DUMMY_PASSWORD_HASH = hash_password("TimingOnly!Password9")


class AuthService:
    def __init__(self, database: Session, settings: Settings) -> None:
        self.database = database
        self.settings = settings

    def signup(
        self,
        *,
        phone: str,
        email: str | None,
        password: str,
        date_of_birth,
        role: Role,
    ) -> User:
        if role != Role.VICTIM:
            raise AuthServiceError(
                403,
                "PRIVILEGED_ROLE_NOT_PUBLIC",
                "Privileged roles require controlled provisioning",
            )

        conditions = [User.phone == phone]
        if email is not None:
            conditions.append(User.email == email)
        if self.database.scalar(select(User.id).where(or_(*conditions))) is not None:
            raise AuthServiceError(
                409,
                "DUPLICATE_ACCOUNT",
                "An account already exists for this phone or email",
            )

        user = User(
            phone=phone,
            email=email,
            password_hash=hash_password(password),
            date_of_birth=date_of_birth,
            role=role,
            status=UserStatus.ACTIVE,
            phone_verified_at=datetime.now(timezone.utc),
            profile_completed=False,
            is_active=True,
        )
        self.database.add(user)
        try:
            self.database.flush()
            self._audit(
                actor_user_id=user.id,
                action="AUTH_SIGNUP",
                resource_id=str(user.id),
                metadata={"role": role.value},
            )
            self.database.commit()
        except IntegrityError as exc:
            self.database.rollback()
            raise AuthServiceError(
                409,
                "DUPLICATE_ACCOUNT",
                "An account already exists for this phone or email",
            ) from exc
        self.database.refresh(user)
        return user

    def login(self, *, identifier: str, password: str) -> IssuedSession:
        user = find_user_by_identifier(self.database, identifier)
        password_valid = verify_password(
            password,
            user.password_hash if user is not None else _DUMMY_PASSWORD_HASH,
        )
        if user is None or not password_valid:
            self._audit(
                actor_user_id=None,
                action="AUTH_LOGIN_FAILED",
                resource_id="unknown",
                metadata={},
            )
            self.database.commit()
            raise AuthServiceError(
                401,
                "INVALID_CREDENTIALS",
                "Invalid login identifier or password",
            )
        self._ensure_account_available(user)

        issued = self._issue_session(user)
        user.last_login_at = datetime.now(timezone.utc)
        self._audit(
            actor_user_id=user.id,
            action="AUTH_LOGIN",
            resource_id=str(user.id),
            metadata={"role": user.role.value, "is_demo": user.is_demo},
        )
        self.database.commit()
        self.database.refresh(user)
        return IssuedSession(
            access_token=issued.access_token,
            refresh_token=issued.refresh_token,
            expires_in=issued.expires_in,
            user=user,
        )

    def create_session_for_user(self, user: User) -> IssuedSession:
        """Issue a normal session after signup without bypassing account status."""
        self._ensure_account_available(user)
        issued = self._issue_session(user)
        self._audit(
            actor_user_id=user.id,
            action="AUTH_SIGNUP_SESSION_ISSUED",
            resource_id=str(user.id),
            metadata={"role": user.role.value, "is_demo": user.is_demo},
        )
        self.database.commit()
        self.database.refresh(user)
        return issued

    def authenticate_access_token(self, token: str) -> User:
        decoded = self._decode_token(token, expected_type="access")
        user = self.database.get(User, decoded.user_id)
        if user is None:
            raise AuthServiceError(401, "INVALID_TOKEN", "Authentication token is invalid")
        self._ensure_token_session(user, decoded.session_version)
        self._ensure_account_available(user)
        return user

    def refresh_session(self, refresh_token: str) -> IssuedSession:
        decoded = self._decode_token(refresh_token, expected_type="refresh")
        user = self.database.get(User, decoded.user_id)
        if user is None:
            raise AuthServiceError(401, "INVALID_REFRESH_TOKEN", "Refresh token is invalid")
        self._ensure_token_session(user, decoded.session_version)
        self._ensure_account_available(user)
        token_hash = self._token_hash(refresh_token)
        expires_at = self._as_utc(user.refresh_token_expires_at)
        if not user.refresh_token_hash or not hmac_compare(user.refresh_token_hash, token_hash):
            raise AuthServiceError(401, "INVALID_REFRESH_TOKEN", "Refresh token is invalid")
        if expires_at is None or expires_at <= datetime.now(timezone.utc):
            raise AuthServiceError(401, "REFRESH_TOKEN_EXPIRED", "Refresh token has expired")

        issued = self._issue_session(user)
        self.database.commit()
        self.database.refresh(user)
        return IssuedSession(
            access_token=issued.access_token,
            refresh_token=issued.refresh_token,
            expires_in=issued.expires_in,
            user=user,
        )

    def logout(self, user: User) -> None:
        user.session_version += 1
        user.refresh_token_hash = None
        user.refresh_token_expires_at = None
        self._audit(
            actor_user_id=user.id,
            action="AUTH_LOGOUT",
            resource_id=str(user.id),
            metadata={"role": user.role.value},
        )
        self.database.commit()

    def _issue_session(self, user: User) -> IssuedSession:
        user.session_version += 1
        now = datetime.now(timezone.utc)
        refresh_expires = now + timedelta(days=self.settings.refresh_token_days)
        refresh_token = self._encode_token(
            user,
            token_type="refresh",
            expires_at=refresh_expires,
            jti=str(uuid.uuid4()),
        )
        user.refresh_token_hash = self._token_hash(refresh_token)
        user.refresh_token_expires_at = refresh_expires
        access_expires = now + timedelta(minutes=self.settings.access_token_minutes)
        access_token = self._encode_token(
            user,
            token_type="access",
            expires_at=access_expires,
            jti=str(uuid.uuid4()),
        )
        return IssuedSession(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.access_token_minutes * 60,
            user=user,
        )

    def _encode_token(
        self,
        user: User,
        *,
        token_type: str,
        expires_at: datetime,
        jti: str,
    ) -> str:
        payload = {
            "sub": str(user.id),
            "role": user.role.value,
            "sv": user.session_version,
            "type": token_type,
            "jti": jti,
            "iss": self.settings.jwt_issuer,
            "aud": self.settings.jwt_audience,
            "iat": datetime.now(timezone.utc),
            "exp": expires_at,
        }
        return jwt.encode(payload, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)

    def _decode_token(self, token: str, *, expected_type: str) -> DecodedToken:
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                audience=self.settings.jwt_audience,
                issuer=self.settings.jwt_issuer,
                options={"require": ["sub", "role", "sv", "type", "jti", "iat", "exp"]},
            )
            if payload["type"] != expected_type:
                raise jwt.InvalidTokenError("Unexpected token type")
            return DecodedToken(
                user_id=int(payload["sub"]),
                role=Role(payload["role"]),
                session_version=int(payload["sv"]),
                token_type=str(payload["type"]),
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthServiceError(401, "TOKEN_EXPIRED", "Authentication token has expired") from exc
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
            raise AuthServiceError(401, "INVALID_TOKEN", "Authentication token is invalid") from exc

    def _ensure_token_session(self, user: User, token_session_version: int) -> None:
        if user.session_version != token_session_version:
            raise AuthServiceError(401, "SESSION_REVOKED", "Authentication session is no longer valid")

    @staticmethod
    def _ensure_account_available(user: User) -> None:
        if not user.is_active or user.status in {UserStatus.SUSPENDED, UserStatus.DISABLED}:
            raise AuthServiceError(403, "ACCOUNT_UNAVAILABLE", "Account is not available for login")

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

    def _audit(
        self,
        *,
        actor_user_id: int | None,
        action: str,
        resource_id: str,
        metadata: dict[str, object],
    ) -> None:
        self.database.add(
            AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                resource_type="authentication",
                resource_id=resource_id,
                metadata_json=metadata,
            )
        )


def hmac_compare(left: str, right: str) -> bool:
    import hmac

    return hmac.compare_digest(left, right)

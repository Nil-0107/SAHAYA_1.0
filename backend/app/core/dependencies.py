"""Shared FastAPI authentication and authorization dependencies."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.models.user import Role, User
from app.services.auth_service import AuthService, AuthServiceError


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_REQUIRED", "message": "Authentication is required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return AuthService(database, settings).authenticate_access_token(credentials.credentials)
    except AuthServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": error.message},
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def _require_ready_account(user: User) -> User:
    if user.phone_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_MOBILE_NOT_VERIFIED",
                "message": "Verify the account mobile before accessing protected features",
            },
        )
    if not user.profile_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PROFILE_INCOMPLETE",
                "message": "Complete profile setup before accessing protected features",
            },
        )
    return user


def get_current_ready_user(user: User = Depends(get_current_user)) -> User:
    return _require_ready_account(user)


def require_roles(*allowed_roles: Role) -> Callable[..., User]:
    def role_dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ROLE_FORBIDDEN", "message": "Account role is not allowed"},
            )
        return _require_ready_account(user)

    return role_dependency


__all__ = ("get_current_ready_user", "get_current_user", "get_db", "require_roles")

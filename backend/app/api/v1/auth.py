"""Authentication routes."""

import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_user
from app.core.rate_limit import RateLimitExceeded, enforce_rate_limit
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    SessionResponse,
    SignupRequest,
    SignupResponse,
    UserResponse,
)
from app.services.auth_service import AuthService, AuthServiceError


router = APIRouter(tags=["auth"])
_REFRESH_COOKIE = "saathi_refresh"
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _service(database: Session, settings: Settings) -> AuthService:
    return AuthService(database, settings)


def _rate_key(request: Request, value: str) -> str:
    client = request.client.host if request.client else "unknown"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{client}:{digest}"


def _enforce(request: Request, value: str, *, limit: int) -> None:
    try:
        enforce_rate_limit(_rate_key(request, value), limit=limit, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail={"code": "RATE_LIMITED", "message": str(exc)}) from exc


def _raise_http_error(error: AuthServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="strict",
        path=_REFRESH_COOKIE_PATH,
    )



@router.post("/auth/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    request: Request,
    response: Response,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SignupResponse:
    _enforce(request, payload.phone, limit=10)
    try:
        service = _service(database, settings)
        user = service.signup(
            phone=payload.phone,
            email=payload.email,
            password=payload.password,
            date_of_birth=payload.date_of_birth,
            role=payload.role,
        )
        session = service.create_session_for_user(user)
    except AuthServiceError as error:
        _raise_http_error(error)
    _set_refresh_cookie(response, session.refresh_token, settings)
    return SignupResponse(
        message="Account created. Complete your profile setup to continue.",
        user=UserResponse.model_validate(session.user),
        verification_required=False,
        access_token=session.access_token,
        expires_in=session.expires_in,
    )


@router.post("/auth/login", response_model=SessionResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SessionResponse:
    _enforce(request, payload.identifier, limit=30)
    try:
        session = _service(database, settings).login(
            identifier=payload.identifier,
            password=payload.password,
        )
    except AuthServiceError as error:
        _raise_http_error(error)
    _set_refresh_cookie(response, session.refresh_token, settings)
    return SessionResponse(
        access_token=session.access_token,
        expires_in=session.expires_in,
        user=UserResponse.model_validate(session.user),
    )


@router.post("/auth/refresh", response_model=SessionResponse)
def refresh(
    request: Request,
    response: Response,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SessionResponse:
    refresh_token = request.cookies.get(_REFRESH_COOKIE)
    if not refresh_token:
        _raise_http_error(
            AuthServiceError(401, "REFRESH_TOKEN_REQUIRED", "Refresh token is required")
        )
    _enforce(request, refresh_token, limit=60)
    try:
        session = _service(database, settings).refresh_session(refresh_token)
    except AuthServiceError as error:
        _raise_http_error(error)
    _set_refresh_cookie(response, session.refresh_token, settings)
    return SessionResponse(
        access_token=session.access_token,
        expires_in=session.expires_in,
        user=UserResponse.model_validate(session.user),
    )


@router.post("/auth/logout", response_model=MessageResponse)
def logout(
    response: Response,
    user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    try:
        _service(database, settings).logout(user)
    except AuthServiceError as error:
        _raise_http_error(error)
    response.delete_cookie(
        key=_REFRESH_COOKIE,
        path=_REFRESH_COOKIE_PATH,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)

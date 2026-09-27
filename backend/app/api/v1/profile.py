"""One-time profile setup and profile read/update routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.profile import (
    AccountMobileStatus,
    ProfileData,
    ProfileResponse,
    ProfileSetupRequest,
    ProfileUpdateRequest,
)
from app.services.auth_service import AuthServiceError
from app.services.profile_service import ProfileService


router = APIRouter(prefix="/profile", tags=["profile"])


def _require_verified_account_mobile(user: User) -> None:
    if user.phone_verified_at is None:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ACCOUNT_MOBILE_NOT_VERIFIED",
                "message": "Verify the account mobile before accessing profile data",
            },
        )


def _response(user: User, profile: ProfileData | None) -> ProfileResponse:
    return ProfileResponse(
        account_mobile=AccountMobileStatus(
            phone=user.phone,
            verified=user.phone_verified_at is not None,
            verified_at=user.phone_verified_at,
        ),
        profile=profile,
        profile_completed=user.profile_completed,
    )


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def setup_profile(
    payload: ProfileSetupRequest,
    user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> ProfileResponse:
    _require_verified_account_mobile(user)
    try:
        profile = ProfileService(database).create(user, payload)
    except AuthServiceError as error:
        raise _http_error(error) from error
    return _response(user, ProfileData.model_validate(profile))


@router.get("", response_model=ProfileResponse)
def get_profile(
    user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> ProfileResponse:
    _require_verified_account_mobile(user)
    profile = ProfileService(database).get(user)
    return _response(
        user,
        ProfileData.model_validate(profile) if profile is not None else None,
    )


@router.patch("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> ProfileResponse:
    _require_verified_account_mobile(user)
    try:
        profile = ProfileService(database).update(user, payload)
    except AuthServiceError as error:
        raise _http_error(error) from error
    return _response(user, ProfileData.model_validate(profile))


def _http_error(error: AuthServiceError):
    from fastapi import HTTPException

    return HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )

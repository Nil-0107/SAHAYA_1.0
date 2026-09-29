"""Authenticated well-being check-in API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_ready_user
from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.models.checkin import Checkin
from app.models.user import User
from app.schemas.checkin import CheckinCreateRequest, CheckinResponse, EmotionClassificationResponse
from app.services.checkin_service import CheckinService, CheckinServiceError


router = APIRouter(prefix="/checkins", tags=["checkins"])


def _raise_service_error(error: CheckinServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


def _response(record: Checkin, *, model_version: str | None = None) -> CheckinResponse:
    return CheckinResponse(
        id=record.id,
        text=record.text,
        case_id=record.case_id,
        class_id=record.predicted_class,
        label=record.predicted_label,
        confidence=record.confidence,
        model_version=model_version or record.model_version,
        analysis_status=record.analysis_status,
        created_at=record.created_at,
        emotion=EmotionClassificationResponse.model_validate(record.emotion_result) if record.emotion_result else None,
    )


@router.post("", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
def create_checkin(
    payload: CheckinCreateRequest,
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CheckinResponse:
    try:
        result = CheckinService(database, include_demo=settings.demo_data_enabled).create(
            user=user,
            text=payload.text,
            case_id=payload.case_id,
        )
    except CheckinServiceError as error:
        _raise_service_error(error)
    return _response(result.record, model_version=result.model_version)


@router.get("/me", response_model=list[CheckinResponse])
def list_my_checkins(
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[CheckinResponse]:
    try:
        records = CheckinService(database, include_demo=settings.demo_data_enabled).list_for_user(user=user)
    except CheckinServiceError as error:
        _raise_service_error(error)
    return [_response(record) for record in records]


@router.get("/{checkin_id}", response_model=CheckinResponse)
def get_checkin(
    checkin_id: int = Path(gt=0),
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CheckinResponse:
    try:
        record = CheckinService(database, include_demo=settings.demo_data_enabled).get_for_user(user=user, checkin_id=checkin_id)
    except CheckinServiceError as error:
        _raise_service_error(error)
    return _response(record)

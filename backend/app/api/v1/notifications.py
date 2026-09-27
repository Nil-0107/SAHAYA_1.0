"""Authenticated notification API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.case import Case
from app.models.case_assignment import CaseAssignment
from app.models.case_document import CaseDocument
from app.models.profile import Profile
from app.models.user import Role
from app.models.notification import Notification
from app.schemas.notification import NotificationTargetDetail, NotificationUserDetail, NotificationCaseDetail

from app.core.dependencies import get_current_ready_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse, ReadAllNotificationsResponse
from app.services.notification_service import NotificationService, NotificationServiceError


router = APIRouter(prefix="/notifications", tags=["notifications"])


def _raise_service_error(error: NotificationServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
) -> list[NotificationResponse]:
    try:
        records = NotificationService(database).list_for_user(user=user)
    except NotificationServiceError as error:
        _raise_service_error(error)
    return [NotificationResponse.model_validate(record) for record in records]


@router.post("/read-all", response_model=ReadAllNotificationsResponse)
def mark_all_notifications_read(
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
) -> ReadAllNotificationsResponse:
    try:
        count = NotificationService(database).mark_all_read(user=user)
    except NotificationServiceError as error:
        _raise_service_error(error)
    return ReadAllNotificationsResponse(updated_count=count)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int = Path(gt=0),
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
) -> NotificationResponse:
    try:
        record = NotificationService(database).mark_read(
            user=user,
            notification_id=notification_id,
        )
    except NotificationServiceError as error:
        _raise_service_error(error)
    return NotificationResponse.model_validate(record)


@router.get("/{notification_id}/target-details", response_model=NotificationTargetDetail)
def notification_target_details(
    notification_id: int = Path(gt=0),
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
) -> NotificationTargetDetail:
    notification = database.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if notification is None:
        raise HTTPException(status_code=404, detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notification not found"})
    if notification.case_id is None:
        raise HTTPException(status_code=404, detail={"code": "NOTIFICATION_NO_CASE", "message": "This notification has no linked case"})
    case = database.get(Case, notification.case_id)
    if case is None:
        raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "Linked case not found"})
    victim = database.get(User, case.owner_user_id)
    if victim is None:
        raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "Help-seeking user not found"})
    allowed = False
    if user.role == Role.VICTIM:
        allowed = victim.id == user.id
    elif user.role == Role.COUNSELLOR:
        allowed = database.scalar(select(CaseAssignment.id).where(CaseAssignment.case_id == case.id, CaseAssignment.assignee_user_id == user.id, CaseAssignment.active.is_(True))) is not None
    elif user.role == Role.DISTRICT_ADMIN:
        allowed = user.district_id is not None and victim.district_id == user.district_id
    elif user.role == Role.STATE_ADMIN:
        allowed = user.state_id is not None and victim.state_id == user.state_id
    elif user.role == Role.NATIONAL_ADMIN:
        allowed = True
    if not allowed:
        raise HTTPException(status_code=403, detail={"code": "NOTIFICATION_SCOPE_FORBIDDEN", "message": "You are not authorised to view this help-seeking user"})
    profile = victim.profile
    if profile is None:
        raise HTTPException(status_code=404, detail={"code": "PROFILE_NOT_FOUND", "message": "User profile not found"})
    docs = list(database.scalars(select(CaseDocument).where(CaseDocument.case_id == case.id).order_by(CaseDocument.uploaded_at.desc())))
    documents = []
    for doc in docs:
        size = None
        if isinstance(doc.extracted_json, dict):
            raw = doc.extracted_json.get("size_bytes")
            if isinstance(raw, int): size = raw
        documents.append({"id": doc.id, "filename": doc.filename, "mime_type": doc.mime_type, "status": doc.status.value, "uploaded_at": doc.uploaded_at, "size_bytes": size, "is_demo": doc.is_demo})
    return NotificationTargetDetail(
        notification=notification,
        user=NotificationUserDetail(id=victim.id, full_name=profile.full_name, display_name=profile.display_name, email=victim.email, phone=victim.phone, date_of_birth=victim.date_of_birth, state_name=victim.state_unit.name if victim.state_unit else None, district_name=victim.district_unit.name if victim.district_unit else None, role=victim.role.value),
        case=NotificationCaseDetail(id=case.id, case_number=case.case_number, category=case.category, status=case.status.value, stage=case.stage, summary=case.summary, protection_request_open=case.protection_request_open, documents=documents),
    )

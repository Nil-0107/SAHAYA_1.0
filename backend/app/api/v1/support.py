"""Role-scoped support request API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_ready_user, require_roles
from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.models.case_assignment import CaseAssignment
from app.models.support_action import SupportAction
from app.models.support_request import SupportRequest, SupportRequestType
from app.models.user import Role, User
from app.schemas.support import (
    SupportAssignmentSummary,
    SupportRequestCreate,
    SupportRequestResponse,
    SupportUpdateResponse,
)
from app.services.support_service import SupportService, SupportServiceError


router = APIRouter(prefix="/support-requests", tags=["support-requests"])

_CATEGORY_BY_TYPE = {
    SupportRequestType.WELLBEING: "counselling",
    SupportRequestType.LEGAL: "legal_help",
    SupportRequestType.PROTECTION: "protection_relocation",
}


def _raise_service_error(error: SupportServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


def _response(request: SupportRequest, database: Session, *, include_demo: bool) -> SupportRequestResponse:
    assignment_query = select(CaseAssignment).where(CaseAssignment.support_request_id == request.id)
    update_query = select(SupportAction).where(SupportAction.support_request_id == request.id)
    if not include_demo:
        assignment_query = assignment_query.where(CaseAssignment.is_demo.is_(False))
        update_query = update_query.where(SupportAction.is_demo.is_(False))
    assignments = list(database.scalars(assignment_query.order_by(CaseAssignment.assigned_at.desc(), CaseAssignment.id.desc())))
    updates = list(database.scalars(update_query.order_by(SupportAction.created_at.asc(), SupportAction.id.asc())))
    return SupportRequestResponse(
        id=request.id,
        case_id=request.case_id,
        category=_CATEGORY_BY_TYPE[request.type],
        status=request.status,
        priority=request.priority,
        details=request.details,
        is_demo=request.is_demo,
        created_at=request.created_at,
        updated_at=request.updated_at,
        resolved_at=request.resolved_at,
        assignments=[
            SupportAssignmentSummary(
                id=assignment.id,
                assignment_type=assignment.assignment_type.value,
                status=assignment.status.value,
                reason=assignment.reason,
                active=assignment.active,
                assigned_at=assignment.assigned_at,
            )
            for assignment in assignments
        ],
        updates=[
            SupportUpdateResponse(
                id=update.id,
                action=update.action,
                status=update.status,
                notes=update.notes,
                created_at=update.created_at,
            )
            for update in updates
        ],
    )


@router.post("", response_model=SupportRequestResponse, status_code=status.HTTP_201_CREATED)
def create_support_request(
    payload: SupportRequestCreate,
    user: User = Depends(require_roles(Role.VICTIM)),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SupportRequestResponse:
    try:
        include_demo = settings.demo_data_enabled
        request = SupportService(database, include_demo=include_demo).create(
            user=user,
            case_id=payload.case_id,
            category=payload.category,
            details=payload.details,
        )
    except SupportServiceError as error:
        _raise_service_error(error)
    return _response(request, database, include_demo=include_demo)


@router.get("/me", response_model=list[SupportRequestResponse])
def list_support_requests(
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[SupportRequestResponse]:
    try:
        include_demo = settings.demo_data_enabled
        requests = SupportService(database, include_demo=include_demo).list_for_user(user=user)
    except SupportServiceError as error:
        _raise_service_error(error)
    return [_response(request, database, include_demo=include_demo) for request in requests]


@router.get("/assigned", response_model=list[SupportRequestResponse])
def list_assigned_support_requests(
    user: User = Depends(require_roles(Role.COUNSELLOR, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[SupportRequestResponse]:
    try:
        include_demo = settings.demo_data_enabled
        requests = SupportService(database, include_demo=include_demo).list_for_user(user=user)
    except SupportServiceError as error:
        _raise_service_error(error)
    return [_response(request, database, include_demo=include_demo) for request in requests]


@router.get("/{request_id}", response_model=SupportRequestResponse)
def get_support_request(
    request_id: int = Path(gt=0),
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SupportRequestResponse:
    try:
        include_demo = settings.demo_data_enabled
        request = SupportService(database, include_demo=include_demo).get_for_user(user=user, request_id=request_id)
    except SupportServiceError as error:
        _raise_service_error(error)
    return _response(request, database, include_demo=include_demo)

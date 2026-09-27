"""Scoped case assignment and staff support-action API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.models.user import Role, User
from app.schemas.assignment import (
    CaseAssignmentCreate,
    CaseAssignmentResponse,
    SupportActionCreate,
    SupportActionResponse,
)
from app.services.assignment_service import AssignmentService, AssignmentServiceError


router = APIRouter(tags=["case-assignments"])


def _raise(error: AssignmentServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


@router.post("/case-assignments", response_model=CaseAssignmentResponse, status_code=201)
def create_case_assignment(
    payload: CaseAssignmentCreate,
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
) -> CaseAssignmentResponse:
    try:
        assignment = AssignmentService(database).create_assignment(
            actor=user,
            support_request_id=payload.support_request_id,
            assignee_user_id=payload.assignee_user_id,
            assignment_type=payload.assignment_type,
            reason=payload.reason,
        )
    except AssignmentServiceError as error:
        database.rollback()
        _raise(error)
    return CaseAssignmentResponse(
        id=assignment.id,
        case_id=assignment.case_id,
        support_request_id=assignment.support_request_id,
        assignee_user_id=assignment.assignee_user_id,
        assigned_by_user_id=assignment.assigned_by_user_id,
        assignment_type=assignment.assignment_type,
        status=assignment.status.value,
        reason=assignment.reason,
        active=assignment.active,
        assigned_at=assignment.assigned_at,
        is_demo=assignment.is_demo,
    )


@router.get("/case-assignments/{case_id}", response_model=list[CaseAssignmentResponse])
def list_case_assignments(
    case_id: int = Path(gt=0),
    user: User = Depends(require_roles(Role.VICTIM, Role.COUNSELLOR, Role.DISTRICT_ADMIN, Role.STATE_ADMIN, Role.NATIONAL_ADMIN)),
    database: Session = Depends(get_db),
) -> list[CaseAssignmentResponse]:
    try:
        assignments = AssignmentService(database).list_assignments(actor=user, case_id=case_id)
    except AssignmentServiceError as error:
        _raise(error)
    return [CaseAssignmentResponse.model_validate(item) for item in assignments]


@router.post("/support-requests/{request_id}/actions", response_model=SupportActionResponse, status_code=201)
def create_support_action(
    request_id: int = Path(gt=0),
    payload: SupportActionCreate | None = None,
    user: User = Depends(require_roles(Role.COUNSELLOR, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
) -> SupportActionResponse:
    if payload is None:
        raise HTTPException(status_code=422, detail={"code": "ACTION_REQUIRED", "message": "Action details are required"})
    try:
        action = AssignmentService(database).add_support_action(
            actor=user,
            support_request_id=request_id,
            action=payload.action,
            notes=payload.notes,
            status=payload.status,
            request_status=payload.request_status,
        )
    except AssignmentServiceError as error:
        database.rollback()
        _raise(error)
    return SupportActionResponse(
        id=action.id,
        support_request_id=action.support_request_id,
        actor_user_id=action.actor_user_id,
        action=action.action,
        status=action.status,
        notes=action.notes,
        created_at=action.created_at,
        is_demo=action.is_demo,
    )

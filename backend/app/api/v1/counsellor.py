"""Counsellor-only dashboard API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.models.user import Role, User
from app.schemas.counsellor import (
    CounsellorAggregate,
    CounsellorDashboardResponse,
    CounsellorFollowUp,
    CounsellorSupportRequest,
    CounsellorUserDetail,
)
from app.schemas.notification import NotificationResponse
from app.services.counsellor_service import CounsellorDashboardService


router = APIRouter(prefix="/counsellor", tags=["counsellor"])


@router.get("/dashboard", response_model=CounsellorDashboardResponse)
def counsellor_dashboard(
    user: User = Depends(require_roles(Role.COUNSELLOR)),
    database: Session = Depends(get_db),
) -> CounsellorDashboardResponse:
    data = CounsellorDashboardService(database).dashboard(user=user)
    return CounsellorDashboardResponse(
        support_requests=[
            CounsellorSupportRequest(
                id=request.id,
                case_id=request.case_id,
                category=request.type.value,
                status=request.status,
                priority=request.priority,
                details=request.details,
                created_at=request.created_at,
                updated_at=request.updated_at,
                is_demo=request.is_demo,
            )
            for request in data["support_requests"]
        ],
        follow_ups=[
            CounsellorFollowUp(
                id=action.id,
                support_request_id=action.support_request_id,
                action=action.action,
                status=action.status,
                notes=action.notes,
                created_at=action.created_at,
                is_demo=action.is_demo,
            )
            for action in data["follow_ups"]
        ],
        support_actions=[
            CounsellorFollowUp(
                id=action.id,
                support_request_id=action.support_request_id,
                action=action.action,
                status=action.status,
                notes=action.notes,
                created_at=action.created_at,
                is_demo=action.is_demo,
            )
            for action in data["support_actions"]
        ],
        notifications=[NotificationResponse.model_validate(item) for item in data["notifications"]],
        aggregate=CounsellorAggregate(**data["aggregate"]),
    )


@router.get("/users", response_model=list[CounsellorUserDetail])
def counsellor_users(
    user: User = Depends(require_roles(Role.COUNSELLOR)),
    database: Session = Depends(get_db),
) -> list[CounsellorUserDetail]:
    return [CounsellorUserDetail(**item) for item in CounsellorDashboardService(database).assigned_users(user=user)]

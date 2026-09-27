"""District Officer dashboard API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.models.user import Role, User
from app.schemas.district import (
    DistrictAggregate,
    DistrictAssistanceRequest,
    DistrictCaseSummary,
    DistrictCoordinationRecord,
    DistrictDashboardResponse,
)
from app.schemas.notification import NotificationResponse
from app.services.district_service import DistrictDashboardService


router = APIRouter(prefix="/district", tags=["district"])

_CATEGORY_BY_TYPE = {
    "wellbeing": "counselling",
    "legal": "legal_help",
    "protection": "protection_relocation",
}


@router.get("/dashboard", response_model=DistrictDashboardResponse)
def district_dashboard(
    user: User = Depends(require_roles(Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
) -> DistrictDashboardResponse:
    data = DistrictDashboardService(database).dashboard(user=user)
    notifications = [NotificationResponse.model_validate(item) for item in data["notifications"]]
    return DistrictDashboardResponse(
        cases=[DistrictCaseSummary.model_validate(item) for item in data["cases"]],
        assistance_requests=[
            DistrictAssistanceRequest(
                id=request.id,
                case_id=request.case_id,
                category=_CATEGORY_BY_TYPE[request.type.value],
                status=request.status,
                priority=request.priority,
                created_at=request.created_at,
                updated_at=request.updated_at,
                is_demo=request.is_demo,
            )
            for request in data["assistance_requests"]
        ],
        coordination=[
            DistrictCoordinationRecord(
                id=assignment.id,
                case_id=assignment.case_id,
                support_request_id=assignment.support_request_id,
                assignment_type=assignment.assignment_type.value,
                status=assignment.status.value,
                reason=assignment.reason,
                active=assignment.active,
                assigned_at=assignment.assigned_at,
                is_demo=assignment.is_demo,
            )
            for assignment in data["coordination"]
        ],
        case_updates=notifications,
        notifications=notifications,
        aggregate=DistrictAggregate(**data["aggregate"]),
    )

"""District Officer dashboard response contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.case import CaseStatus
from app.models.support_request import SupportRequestStatus
from app.schemas.notification import NotificationResponse


class DistrictCaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    stage: str
    status: CaseStatus
    category_verified: bool
    next_hearing: datetime | None
    is_demo: bool


class DistrictAssistanceRequest(BaseModel):
    id: int
    case_id: int
    category: str
    status: SupportRequestStatus
    priority: str
    created_at: datetime
    updated_at: datetime
    is_demo: bool


class DistrictCoordinationRecord(BaseModel):
    id: int
    case_id: int
    support_request_id: int
    assignment_type: str
    status: str
    reason: str
    active: bool
    assigned_at: datetime
    is_demo: bool


class DistrictAggregate(BaseModel):
    authorized_case_count: int
    open_assistance_request_count: int
    active_coordination_count: int
    protection_request_count: int
    unread_notification_count: int


class DistrictDashboardResponse(BaseModel):
    cases: list[DistrictCaseSummary]
    assistance_requests: list[DistrictAssistanceRequest]
    coordination: list[DistrictCoordinationRecord]
    case_updates: list[NotificationResponse]
    notifications: list[NotificationResponse]
    aggregate: DistrictAggregate

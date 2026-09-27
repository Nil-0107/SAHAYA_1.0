"""Counsellor dashboard response contracts."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.support_action import SupportActionStatus
from app.models.support_request import SupportRequestStatus
from app.schemas.notification import NotificationResponse


class CounsellorSupportRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    category: str
    status: SupportRequestStatus
    priority: str
    details: str
    created_at: datetime
    updated_at: datetime
    is_demo: bool


class CounsellorFollowUp(BaseModel):
    id: int
    support_request_id: int
    action: str
    status: SupportActionStatus
    notes: str
    created_at: datetime
    is_demo: bool


class CounsellorAggregate(BaseModel):
    assigned_request_count: int
    open_follow_up_count: int
    support_action_count: int
    resolved_request_count: int
    unread_notification_count: int


class CounsellorDashboardResponse(BaseModel):
    support_requests: list[CounsellorSupportRequest]
    follow_ups: list[CounsellorFollowUp]
    support_actions: list[CounsellorFollowUp]
    notifications: list[NotificationResponse]
    aggregate: CounsellorAggregate


class CounsellorUserDetail(BaseModel):
    id: int
    full_name: str
    display_name: str
    email: str | None
    phone: str
    date_of_birth: date | None
    district_name: str | None
    case_id: int
    case_number: str
    support_request_id: int
    support_category: str
    support_status: SupportRequestStatus
    last_checkin_at: datetime | None
    is_demo: bool

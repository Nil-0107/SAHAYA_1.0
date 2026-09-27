"""Administrator aggregate dashboard response contracts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.notification import NotificationResponse
from app.services.priority_service import AdministrativePriority


class AdminAggregate(BaseModel):
    total_case_count: int
    active_case_count: int
    total_support_request_count: int
    open_support_request_count: int
    resolved_support_request_count: int
    active_assignment_count: int
    district_count: int
    total_checkin_count: int
    total_user_count: int
    active_user_count: int
    unread_admin_notification_count: int


class AdminDistrictAnalytics(BaseModel):
    district: str
    case_count: int
    active_case_count: int
    support_request_count: int
    open_support_request_count: int
    high_priority_request_count: int
    active_assignment_count: int
    is_demo: bool


class AdminSupportCountBucket(BaseModel):
    label: str
    count: int


class AdminSupportRequestCounts(BaseModel):
    by_type: list[AdminSupportCountBucket]
    by_status: list[AdminSupportCountBucket]


class AdminPriorityFactors(BaseModel):
    verified_high_priority_category: bool
    open_protection_request: bool
    explicit_human_support_request: bool
    verified_wellbeing_review_flag: bool


class AdminPriorityQueueItem(BaseModel):
    case_id: int
    case_number: str
    district: str
    category: str
    category_verified: bool
    priority: AdministrativePriority
    explanation: str
    reasons: list[str]
    factors: AdminPriorityFactors
    is_demo: bool


class AdminAuditEntry(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    resource_type: str
    resource_id: str
    metadata: dict[str, Any]
    created_at: datetime
    is_demo: bool


class AdminEscalationTrendPoint(BaseModel):
    date: date
    request_count: int
    open_count: int
    resolved_count: int


class AdminDashboardResponse(BaseModel):
    aggregate: AdminAggregate
    district_analytics: list[AdminDistrictAnalytics]
    support_request_counts: AdminSupportRequestCounts
    priority_queue: list[AdminPriorityQueueItem]
    escalation_trends: list[AdminEscalationTrendPoint]
    notifications: list[NotificationResponse]
    audit_entries: list[AdminAuditEntry]


class AdminUserDetail(BaseModel):
    id: int
    full_name: str
    display_name: str
    email: str | None
    phone: str
    date_of_birth: date | None
    role: str
    status: str
    state_id: int | None
    district_id: int | None
    state_name: str | None
    district_name: str | None
    case_count: int
    open_case_count: int
    support_request_count: int
    last_checkin_at: datetime | None
    is_demo: bool

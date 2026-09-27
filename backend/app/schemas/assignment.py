"""Case assignment and support-action workflow contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.case_assignment import AssignmentType
from app.models.support_action import SupportActionStatus
from app.models.support_request import SupportRequestStatus


class CaseAssignmentCreate(BaseModel):
    support_request_id: int = Field(gt=0)
    assignee_user_id: int = Field(gt=0)
    assignment_type: AssignmentType
    reason: str = Field(min_length=2, max_length=1000)


class CaseAssignmentResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    case_id: int
    support_request_id: int
    assignee_user_id: int
    assigned_by_user_id: int
    assignment_type: AssignmentType
    status: str
    reason: str
    active: bool
    assigned_at: datetime
    is_demo: bool


class SupportActionCreate(BaseModel):
    action: str = Field(min_length=2, max_length=120)
    notes: str = Field(min_length=1, max_length=4000)
    status: SupportActionStatus = SupportActionStatus.RECORDED
    request_status: SupportRequestStatus | None = None


class SupportActionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    support_request_id: int
    actor_user_id: int
    action: str
    status: SupportActionStatus
    notes: str
    created_at: datetime
    is_demo: bool

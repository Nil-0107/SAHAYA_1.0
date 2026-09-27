"""Support request request/response contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.support_action import SupportActionStatus
from app.models.support_request import SupportRequestStatus


class SupportCategory(str, Enum):
    COUNSELLING = "counselling"
    LEGAL_HELP = "legal_help"
    PROTECTION_RELOCATION = "protection_relocation"


class SupportRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: int = Field(gt=0)
    category: SupportCategory
    details: str = Field(min_length=1, max_length=4000)

    @field_validator("details")
    @classmethod
    def normalize_details(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Support request details must not be empty")
        return normalized


class SupportAssignmentSummary(BaseModel):
    id: int
    assignment_type: str
    status: str
    reason: str
    active: bool
    assigned_at: datetime


class SupportUpdateResponse(BaseModel):
    id: int
    action: str
    status: SupportActionStatus
    notes: str
    created_at: datetime


class SupportRequestResponse(BaseModel):
    id: int
    case_id: int
    category: SupportCategory
    status: SupportRequestStatus
    priority: str
    details: str
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    assignments: list[SupportAssignmentSummary]
    updates: list[SupportUpdateResponse]

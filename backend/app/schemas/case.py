"""Case and document response contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.case import CaseStatus
from app.models.case_document import DocumentStatus


class CaseCreate(BaseModel):
    category: str = Field(default="general_support", min_length=2, max_length=80)
    summary: str | None = Field(default=None, max_length=4000)


class CaseDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    mime_type: str
    status: DocumentStatus
    uploaded_at: datetime
    size_bytes: int | None = None
    is_demo: bool


class CaseSupportSummary(BaseModel):
    id: int
    type: str
    status: str
    priority: str
    is_demo: bool


class CaseUpdate(BaseModel):
    date: str
    label: str
    is_demo: bool = True


class CaseTimelineEvent(BaseModel):
    date: str
    label: str
    is_demo: bool = True


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    category: str
    category_verified: bool
    status: CaseStatus
    stage: str
    court_name: str | None
    next_hearing: datetime | None
    summary: str | None
    protection_request_open: bool
    created_at: datetime
    is_demo: bool
    documents: list[CaseDocumentResponse]
    support_information: list[CaseSupportSummary]
    updates: list[CaseUpdate]
    timeline: list[CaseTimelineEvent]

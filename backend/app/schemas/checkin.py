"""Check-in request and response contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.checkin import CheckinAnalysisStatus


class CheckinCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    case_id: int | None = Field(default=None, gt=0)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Check-in text must not be empty")
        return normalized


class CheckinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    case_id: int | None
    class_id: int | None
    label: str | None
    confidence: float | None
    model_version: str | None
    analysis_status: CheckinAnalysisStatus
    created_at: datetime

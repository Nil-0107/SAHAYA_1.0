"""AI conversation request and response contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.ai_conversation import AIConversationStatus
from app.models.ai_message import AIMessageRole, AIMessageStatus


class AIChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: int | None = Field(default=None, gt=0)
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Message must not be empty")
        return normalized


class AIChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: AIMessageRole
    status: AIMessageStatus
    content: str
    created_at: datetime


class AIChatResponse(BaseModel):
    conversation_id: int
    conversation_status: AIConversationStatus
    source: Literal["gemini", "fallback"]
    model_version: str | None
    immediate_danger: bool
    user_message: AIChatMessageResponse
    assistant_message: AIChatMessageResponse


class AIVoiceResponse(BaseModel):
    transcript: str
    source: Literal["gemini", "unavailable"]
    model_version: str | None

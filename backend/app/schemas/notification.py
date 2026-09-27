"""Notification response contracts."""

from __future__ import annotations

from datetime import datetime
import datetime as datetime_module

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int | None
    type: str
    title: str
    message: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    is_demo: bool


class NotificationUserDetail(BaseModel):
    id: int
    full_name: str
    display_name: str
    email: str | None
    phone: str
    date_of_birth: datetime_module.date | None
    state_name: str | None
    district_name: str | None
    role: str

class NotificationCaseDetail(BaseModel):
    id: int
    case_number: str
    category: str
    status: str
    stage: str
    summary: str | None
    protection_request_open: bool
    documents: list[dict[str, object]]

class NotificationTargetDetail(BaseModel):
    notification: NotificationResponse
    user: NotificationUserDetail
    case: NotificationCaseDetail | None

class ReadAllNotificationsResponse(BaseModel):
    updated_count: int

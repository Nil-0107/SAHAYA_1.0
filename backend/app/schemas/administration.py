"""Administrative provisioning request and response contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.phones import PhoneNumberError, normalize_account_mobile
from app.models.user import Role, UserStatus


class AdministrativeAccountCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    display_name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=255)
    phone: str = Field(min_length=10, max_length=16)
    password: str = Field(min_length=12, max_length=256)
    language: str = Field(default="English", min_length=2, max_length=40)
    state_id: int | None = Field(default=None, gt=0)
    district_id: int | None = Field(default=None, gt=0)
    state_name: str | None = Field(default=None, min_length=2, max_length=160)
    district_name: str | None = Field(default=None, min_length=2, max_length=160)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if "@" not in normalized:
            raise ValueError("A valid email address is required")
        return normalized

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        try:
            return normalize_account_mobile(value)
        except PhoneNumberError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not (
            any(character.islower() for character in value)
            and any(character.isupper() for character in value)
            and any(character.isdigit() for character in value)
            and any(not character.isalnum() for character in value)
        ):
            raise ValueError("Password must include lowercase, uppercase, number, and symbol characters")
        return value


class AdministrativeAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    display_name: str
    email: str | None
    phone: str
    role: Role
    status: UserStatus
    state_id: int | None
    district_id: int | None
    state_name: str | None
    district_name: str | None
    created_by_user_id: int | None
    created_role: Role | None
    appointed_by_user_id: int | None
    appointed_at: datetime | None
    created_at: datetime
    is_demo: bool


class AdministrativeUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit_type: str
    parent_id: int | None
    is_demo: bool


class AccountStatusUpdate(BaseModel):
    status: UserStatus

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: UserStatus) -> UserStatus:
        if value not in {UserStatus.ACTIVE, UserStatus.SUSPENDED}:
            raise ValueError("Only active or suspended status can be set here")
        return value

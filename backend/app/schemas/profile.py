"""One-time profile setup and explicit profile update schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileSetupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    display_name: str = Field(min_length=1, max_length=80)
    preferred_language: str = Field(min_length=2, max_length=40)
    city_or_district: str = Field(min_length=2, max_length=120)
    emergency_contact_name: str | None = Field(default=None, max_length=120)
    emergency_contact_phone: str | None = Field(default=None, min_length=10, max_length=20)
    safe_contact_method: str | None = Field(default=None, max_length=80)
    address: str | None = Field(default=None, max_length=255)
    case_reference: str | None = Field(default=None, max_length=120)
    relationship_to_case: str | None = Field(default=None, max_length=120)
    role_in_case: str | None = Field(default=None, max_length=120)
    consent: Literal[True]

    @model_validator(mode="after")
    def validate_emergency_contact_pair(self) -> "ProfileSetupRequest":
        if bool(self.emergency_contact_name) != bool(self.emergency_contact_phone):
            raise ValueError(
                "Emergency contact name and phone must be provided together"
            )
        return self


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=40)
    city_or_district: str | None = Field(default=None, min_length=2, max_length=120)
    emergency_contact_name: str | None = Field(default=None, max_length=120)
    emergency_contact_phone: str | None = Field(default=None, min_length=10, max_length=20)
    safe_contact_method: str | None = Field(default=None, max_length=80)
    address: str | None = Field(default=None, max_length=255)
    case_reference: str | None = Field(default=None, max_length=120)
    relationship_to_case: str | None = Field(default=None, max_length=120)
    role_in_case: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_emergency_contact_pair(self) -> "ProfileUpdateRequest":
        if self.emergency_contact_name is not None or self.emergency_contact_phone is not None:
            if not self.emergency_contact_name or not self.emergency_contact_phone:
                raise ValueError(
                    "Emergency contact name and phone must be provided together"
                )
        return self


class AccountMobileStatus(BaseModel):
    phone: str
    verified: bool
    verified_at: datetime | None


class ProfileData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    display_name: str
    preferred_language: str
    city_or_district: str
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    safe_contact_method: str | None
    address: str | None
    case_reference: str | None
    relationship_to_case: str | None
    role_in_case: str | None
    consent_at: datetime


class ProfileResponse(BaseModel):
    account_mobile: AccountMobileStatus
    profile: ProfileData | None
    profile_completed: bool

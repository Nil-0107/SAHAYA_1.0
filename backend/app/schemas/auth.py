"""Authentication request and response contracts."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.phones import PhoneNumberError, normalize_account_mobile
from app.models.user import Role, UserStatus


class SignupRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=16)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=8, max_length=256)
    date_of_birth: date = Field()
    role: Role = Role.VICTIM

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        try:
            return normalize_account_mobile(value)
        except PhoneNumberError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().casefold()
        if not normalized or "@" not in normalized or len(normalized) > 255:
            raise ValueError("Email must be a valid email address")
        return normalized

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value: date) -> date:
        from datetime import date as _date
        if value >= _date.today():
            raise ValueError("Date of birth must be in the past")
        if value.year < 1900:
            raise ValueError("Date of birth is invalid")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if (
            len(value) < 8
            or not any(character.islower() for character in value)
            or not any(character.isupper() for character in value)
            or not any(character.isdigit() for character in value)
            or not any(not character.isalnum() for character in value)
        ):
            raise ValueError(
                "Password must include lowercase, uppercase, number, and symbol characters"
            )
        return value


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("identifier")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if "@" in normalized:
            return normalized
        try:
            return normalize_account_mobile(normalized)
        except PhoneNumberError as exc:
            raise ValueError(str(exc)) from exc


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    date_of_birth: date | None
    email: str | None
    role: Role
    state_id: int | None = None
    district_id: int | None = None
    status: UserStatus
    phone_verified_at: datetime | None
    profile_completed: bool
    is_demo: bool


class SignupResponse(BaseModel):
    message: str
    user: UserResponse
    verification_required: bool
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class OTPStartRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=16)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        try:
            return normalize_account_mobile(value)
        except PhoneNumberError as exc:
            raise ValueError(str(exc)) from exc


class OTPResendRequest(OTPStartRequest):
    pass


class OTPVerifyRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=16)
    code: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        try:
            return normalize_account_mobile(value)
        except PhoneNumberError as exc:
            raise ValueError(str(exc)) from exc


class OTPStatusResponse(BaseModel):
    success: bool = True
    message: str


class OTPVerifyResponse(BaseModel):
    success: bool = True
    message: str

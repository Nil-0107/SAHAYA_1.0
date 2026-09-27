"""One-time profile setup and explicit profile update service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.administrative_unit import AdministrativeUnit
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ProfileSetupRequest, ProfileUpdateRequest
from app.services.auth_service import AuthServiceError


class ProfileService:
    def __init__(self, database: Session) -> None:
        self.database = database

    def create(self, user: User, payload: ProfileSetupRequest) -> Profile:
        if user.phone_verified_at is None:
            raise AuthServiceError(
                403,
                "ACCOUNT_MOBILE_NOT_VERIFIED",
                "Verify the signed-in account mobile before profile setup",
            )
        if user.profile_completed or user.profile is not None:
            raise AuthServiceError(
                409,
                "PROFILE_ALREADY_COMPLETED",
                "Profile setup has already been completed",
            )

        district_unit = self.database.scalar(
            select(AdministrativeUnit).where(
                AdministrativeUnit.unit_type == "district",
                AdministrativeUnit.name.ilike(payload.city_or_district.strip()),
            )
        )
        if district_unit is not None:
            user.district_id = district_unit.id
            user.state_id = district_unit.parent_id

        profile = Profile(
            user_id=user.id,
            full_name=payload.full_name.strip(),
            display_name=payload.display_name.strip(),
            preferred_language=payload.preferred_language.strip(),
            city_or_district=payload.city_or_district.strip(),
            emergency_contact_name=self._clean_optional(payload.emergency_contact_name),
            emergency_contact_phone=self._clean_optional(payload.emergency_contact_phone),
            safe_contact_method=self._clean_optional(payload.safe_contact_method),
            address=self._clean_optional(payload.address),
            case_reference=self._clean_optional(payload.case_reference),
            relationship_to_case=self._clean_optional(payload.relationship_to_case),
            role_in_case=self._clean_optional(payload.role_in_case),
            consent_at=datetime.now(timezone.utc),
        )
        self.database.add(profile)
        user.profile_completed = True
        self.database.flush()
        self._audit(user.id, "PROFILE_SETUP_COMPLETED")
        try:
            self.database.commit()
        except IntegrityError as exc:
            self.database.rollback()
            raise AuthServiceError(
                409,
                "PROFILE_ALREADY_COMPLETED",
                "Profile setup has already been completed",
            ) from exc
        self.database.refresh(profile)
        return profile

    def update(self, user: User, payload: ProfileUpdateRequest) -> Profile:
        profile = self.database.scalar(
            select(Profile).where(Profile.user_id == user.id)
        )
        if not user.profile_completed or profile is None:
            raise AuthServiceError(
                409,
                "PROFILE_NOT_COMPLETED",
                "Complete one-time profile setup before updating the profile",
            )
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(profile, field, self._clean_optional(value) if isinstance(value, str) else value)
        profile.updated_at = datetime.now(timezone.utc)
        self._audit(user.id, "PROFILE_UPDATED", {"fields": sorted(payload.model_fields_set)})
        self.database.commit()
        self.database.refresh(profile)
        return profile

    def get(self, user: User) -> Profile | None:
        return self.database.scalar(select(Profile).where(Profile.user_id == user.id))

    def _audit(
        self,
        user_id: int,
        action: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.database.add(
            AuditLog(
                actor_user_id=user_id,
                action=action,
                resource_type="profile",
                resource_id=str(user_id),
                metadata_json=metadata or {},
            )
        )

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

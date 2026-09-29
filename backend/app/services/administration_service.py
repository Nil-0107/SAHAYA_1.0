"""Secure hierarchical administrator provisioning and account status service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.administrative_unit import AdministrativeUnit
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.profile import Profile
from app.models.user import Role, User, UserStatus
from app.schemas.administration import (
    AccountStatusUpdate,
    AdministrativeAccountCreate,
)


class AdministrationError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AdministrationService:
    def __init__(self, database: Session) -> None:
        self.database = database

    def create_state_admin(
        self,
        *,
        actor: User,
        payload: AdministrativeAccountCreate,
    ) -> User:
        self._require_role(actor, Role.NATIONAL_ADMIN)
        state = self._resolve_state_for_national(payload)
        return self._create_account(
            actor=actor,
            role=Role.STATE_ADMIN,
            payload=payload,
            state=state,
            district=None,
            created_by=True,
            appointed_by=False,
            audit_action="STATE_ADMIN_CREATED",
        )

    def create_district_admin(
        self,
        *,
        actor: User,
        payload: AdministrativeAccountCreate,
    ) -> User:
        self._require_role(actor, Role.STATE_ADMIN)
        if payload.state_id is None or actor.state_id != payload.state_id:
            raise AdministrationError(403, "GEOGRAPHIC_SCOPE_FORBIDDEN", "District administrator must be created within your state")
        state = self._unit(payload.state_id, expected_type="state")
        district = self._resolve_district(payload, state=state)
        return self._create_account(
            actor=actor,
            role=Role.DISTRICT_ADMIN,
            payload=payload,
            state=state,
            district=district,
            created_by=True,
            appointed_by=False,
            audit_action="DISTRICT_ADMIN_CREATED",
        )

    def create_counsellor(
        self,
        *,
        actor: User,
        payload: AdministrativeAccountCreate,
    ) -> User:
        self._require_role(actor, Role.DISTRICT_ADMIN)
        if payload.district_id is None or actor.district_id != payload.district_id:
            raise AdministrationError(403, "GEOGRAPHIC_SCOPE_FORBIDDEN", "Counsellor must be appointed within your district")
        district = self._unit(payload.district_id, expected_type="district")
        state = self._unit(district.parent_id, expected_type="state")
        return self._create_account(
            actor=actor,
            role=Role.COUNSELLOR,
            payload=payload,
            state=state,
            district=district,
            created_by=False,
            appointed_by=True,
            audit_action="COUNSELLOR_APPOINTED",
        )

    def list_accounts(self, *, actor: User, role: Role) -> list[User]:
        query = select(User).where(User.role == role, User.is_demo.is_(False))
        if role == Role.STATE_ADMIN:
            self._require_role(actor, Role.NATIONAL_ADMIN)
        elif role == Role.DISTRICT_ADMIN:
            self._require_role(actor, Role.STATE_ADMIN)
            query = query.where(User.state_id == actor.state_id)
        elif role == Role.COUNSELLOR:
            self._require_role(actor, Role.DISTRICT_ADMIN)
            query = query.where(User.district_id == actor.district_id)
        else:
            raise AdministrationError(403, "ROLE_FORBIDDEN", "Account role is not manageable")
        return list(self.database.scalars(query.order_by(User.created_at.desc(), User.id.desc())))

    def update_status(
        self,
        *,
        actor: User,
        target_user_id: int,
        payload: AccountStatusUpdate,
    ) -> User:
        target = self.database.get(User, target_user_id)
        if target is None:
            raise AdministrationError(404, "ACCOUNT_NOT_FOUND", "Account not found")
        if target.id == actor.id:
            raise AdministrationError(403, "SELF_STATUS_CHANGE_FORBIDDEN", "You cannot change your own account status")
        expected: dict[Role, tuple[Role, ...]] = {
            Role.NATIONAL_ADMIN: (Role.STATE_ADMIN,),
            Role.STATE_ADMIN: (Role.DISTRICT_ADMIN,),
            Role.DISTRICT_ADMIN: (Role.COUNSELLOR,),
        }
        if actor.role not in expected or target.role not in expected[actor.role]:
            raise AdministrationError(403, "ROLE_FORBIDDEN", "You cannot manage this account")
        if actor.role == Role.STATE_ADMIN and target.state_id != actor.state_id:
            raise AdministrationError(403, "GEOGRAPHIC_SCOPE_FORBIDDEN", "Account is outside your state")
        if actor.role == Role.DISTRICT_ADMIN and target.district_id != actor.district_id:
            raise AdministrationError(403, "GEOGRAPHIC_SCOPE_FORBIDDEN", "Account is outside your district")
        previous = target.status
        target.status = payload.status
        target.is_active = payload.status == UserStatus.ACTIVE
        self.database.add(
            AuditLog(
                actor_user_id=actor.id,
                action="ADMIN_ACCOUNT_STATUS_UPDATED",
                resource_type="user",
                resource_id=str(target.id),
                metadata_json={
                    "target_role": target.role.value,
                    "previous_status": previous.value,
                    "new_status": payload.status.value,
                },
            )
        )
        self.database.commit()
        self.database.refresh(target)
        return target

    def list_units(self, *, actor: User, unit_type: str) -> list[AdministrativeUnit]:
        if unit_type == "state":
            self._require_role(actor, Role.NATIONAL_ADMIN, Role.STATE_ADMIN)
        elif unit_type == "district":
            self._require_role(actor, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)
            query = select(AdministrativeUnit).where(AdministrativeUnit.unit_type == unit_type)
            if actor.role == Role.STATE_ADMIN:
                query = query.where(AdministrativeUnit.parent_id == actor.state_id)
            else:
                query = query.where(AdministrativeUnit.id == actor.district_id)
            return list(self.database.scalars(query.order_by(AdministrativeUnit.name)))
        else:
            raise AdministrationError(422, "UNIT_TYPE_INVALID", "Unsupported administrative unit type")
        return list(
            self.database.scalars(
                select(AdministrativeUnit)
                .where(AdministrativeUnit.unit_type == unit_type)
                .order_by(AdministrativeUnit.name)
            )
        )

    def _create_account(
        self,
        *,
        actor: User,
        role: Role,
        payload: AdministrativeAccountCreate,
        state: AdministrativeUnit,
        district: AdministrativeUnit | None,
        created_by: bool,
        appointed_by: bool,
        audit_action: str,
    ) -> User:
        self._assert_unique(payload.email, payload.phone)
        now = datetime.now(timezone.utc)
        user = User(
            email=payload.email,
            phone=payload.phone,
            password_hash=hash_password(payload.password),
            role=role,
            status=UserStatus.ACTIVE,
            phone_verified_at=now,
            profile_completed=True,
            is_active=True,
            state_id=state.id,
            district_id=district.id if district else None,
            created_by_user_id=actor.id if created_by else None,
            created_role=role,
            appointed_by_user_id=actor.id if appointed_by else None,
            appointed_at=now if appointed_by else None,
        )
        self.database.add(user)
        self.database.flush()
        self.database.add(
            Profile(
                user_id=user.id,
                full_name=payload.full_name,
                display_name=payload.display_name,
                preferred_language=payload.language,
                city_or_district=district.name if district else state.name,
                consent_at=now,
            )
        )
        self.database.add(
            Notification(
                user_id=user.id,
                type="administrative_account",
                title="Administrator account created" if role != Role.COUNSELLOR else "Counsellor appointment",
                message=(
                    "Your administrator account has been created."
                    if role == Role.STATE_ADMIN
                    else "You have been registered as District Administrator."
                    if role == Role.DISTRICT_ADMIN
                    else "You have been appointed as a counsellor for your district."
                ),
            )
        )
        self.database.add(
            AuditLog(
                actor_user_id=actor.id,
                action=audit_action,
                resource_type="user",
                resource_id=str(user.id),
                metadata_json={
                    "created_role": role.value,
                    "state_id": str(state.id),
                    "district_id": str(district.id) if district else None,
                },
            )
        )
        self.database.commit()
        self.database.refresh(user)
        return user

    def _resolve_state_for_national(self, payload: AdministrativeAccountCreate) -> AdministrativeUnit:
        if payload.state_id is not None:
            return self._unit(payload.state_id, expected_type="state")
        if not payload.state_name:
            raise AdministrationError(422, "STATE_REQUIRED", "State is required")
        state = self.database.scalar(
            select(AdministrativeUnit).where(
                AdministrativeUnit.unit_type == "state",
                AdministrativeUnit.name == payload.state_name.strip(),
            )
        )
        if state is not None:
            return state
        state = AdministrativeUnit(name=payload.state_name.strip(), unit_type="state")
        self.database.add(state)
        self.database.flush()
        return state

    def _resolve_district(
        self,
        payload: AdministrativeAccountCreate,
        *,
        state: AdministrativeUnit,
    ) -> AdministrativeUnit:
        if payload.district_id is not None:
            district = self._unit(payload.district_id, expected_type="district")
            if district.parent_id != state.id:
                raise AdministrationError(403, "GEOGRAPHIC_SCOPE_FORBIDDEN", "District is outside the selected state")
            return district
        if not payload.district_name:
            raise AdministrationError(422, "DISTRICT_REQUIRED", "District is required")
        name = payload.district_name.strip()
        district = self.database.scalar(
            select(AdministrativeUnit).where(
                AdministrativeUnit.unit_type == "district",
                AdministrativeUnit.parent_id == state.id,
                AdministrativeUnit.name == name,
            )
        )
        if district is not None:
            return district
        district = AdministrativeUnit(name=name, unit_type="district", parent_id=state.id)
        self.database.add(district)
        self.database.flush()
        return district

    def _assert_unique(self, email: str, phone: str) -> None:
        existing = self.database.scalar(
            select(User).where((User.email == email) | (User.phone == phone))
        )
        if existing is not None:
            raise AdministrationError(409, "ACCOUNT_ALREADY_EXISTS", "An account with this email or mobile already exists")

    def _unit(self, unit_id: int | None, *, expected_type: str) -> AdministrativeUnit:
        if unit_id is None:
            raise AdministrationError(422, "GEOGRAPHIC_SCOPE_REQUIRED", "Administrative scope is required")
        unit = self.database.get(AdministrativeUnit, unit_id)
        if unit is None or unit.unit_type != expected_type:
            raise AdministrationError(422, "GEOGRAPHIC_SCOPE_INVALID", "Administrative scope is invalid")
        return unit

    def _require_role(self, actor: User, *roles: Role) -> None:
        if actor.role not in roles:
            raise AdministrationError(403, "ROLE_FORBIDDEN", "Account role is not allowed for this action")

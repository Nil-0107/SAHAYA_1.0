"""User account model, supported roles, and account status."""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin


class Role(str, Enum):
    VICTIM = "victim"
    COUNSELLOR = "counsellor"
    DISTRICT_ADMIN = "district_admin"
    STATE_ADMIN = "state_admin"
    NATIONAL_ADMIN = "national_admin"

    # Backwards-compatible database aliases for existing local databases. New
    # application code uses the explicit administrative role names above.
    DISTRICT_OFFICER = "district_admin"
    ADMIN = "national_admin"


class UserStatus(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


def enum_column(enum_type: type[Enum], name: str) -> SqlEnum:
    return SqlEnum(
        enum_type,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda values: [value.value for value in values],
        validate_strings=True,
    )


class User(DemoRecordMixin, Base):
    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    role: Mapped[Role] = mapped_column(enum_column(Role, "user_role"), nullable=False, index=True)
    state_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_units.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    district_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_units.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_role: Mapped[Role | None] = mapped_column(enum_column(Role, "created_user_role"), nullable=True)
    appointed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    appointed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        enum_column(UserStatus, "user_status"),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
        server_default=UserStatus.PENDING_VERIFICATION.value,
        index=True,
    )
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    profile_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    session_version: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    refresh_token_hash: Mapped[str | None] = mapped_column(String(64))
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    state_unit: Mapped["AdministrativeUnit | None"] = relationship(
        "AdministrativeUnit", foreign_keys=[state_id], lazy="joined"
    )
    district_unit: Mapped["AdministrativeUnit | None"] = relationship(
        "AdministrativeUnit", foreign_keys=[district_id], lazy="joined"
    )
    created_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[created_by_user_id], remote_side="User.id"
    )
    appointed_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[appointed_by_user_id], remote_side="User.id"
    )
    created_accounts: Mapped[list["User"]] = relationship(
        "User", foreign_keys=[created_by_user_id], back_populates="created_by"
    )
    appointed_accounts: Mapped[list["User"]] = relationship(
        "User", foreign_keys=[appointed_by_user_id], back_populates="appointed_by"
    )

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    owned_cases: Mapped[list["Case"]] = relationship(
        back_populates="owner", foreign_keys="Case.owner_user_id"
    )
    owned_case_documents: Mapped[list["CaseDocument"]] = relationship(
        back_populates="owner", foreign_keys="CaseDocument.owner_user_id"
    )
    checkins: Mapped[list["Checkin"]] = relationship(
        back_populates="user", foreign_keys="Checkin.user_id"
    )
    support_requests: Mapped[list["SupportRequest"]] = relationship(
        back_populates="user", foreign_keys="SupportRequest.user_id"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", foreign_keys="Notification.user_id"
    )
    ai_conversations: Mapped[list["AIConversation"]] = relationship(
        back_populates="user", foreign_keys="AIConversation.user_id"
    )
    assignments_received: Mapped[list["CaseAssignment"]] = relationship(
        back_populates="assignee",
        foreign_keys="CaseAssignment.assignee_user_id",
    )
    assignments_created: Mapped[list["CaseAssignment"]] = relationship(
        back_populates="assigned_by",
        foreign_keys="CaseAssignment.assigned_by_user_id",
    )
    support_actions: Mapped[list["SupportAction"]] = relationship(
        back_populates="actor", foreign_keys="SupportAction.actor_user_id"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="actor", foreign_keys="AuditLog.actor_user_id"
    )

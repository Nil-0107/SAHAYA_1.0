"""Case/support assignment model and assignment status."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin, utc_now
from app.models.user import enum_column


class AssignmentType(str, Enum):
    WELLBEING_COUNSELLOR = "wellbeing_counsellor"
    DISTRICT_COORDINATION = "district_coordination"


class AssignmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    REVOKED = "revoked"


class CaseAssignment(DemoRecordMixin, Base):
    __tablename__ = "case_assignments"

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    support_request_id: Mapped[int] = mapped_column(
        ForeignKey("support_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignee_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assignment_type: Mapped[AssignmentType] = mapped_column(
        enum_column(AssignmentType, "case_assignment_type"), nullable=False, index=True
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        enum_column(AssignmentStatus, "case_assignment_status"),
        nullable=False,
        default=AssignmentStatus.ACTIVE,
        server_default=AssignmentStatus.ACTIVE.value,
        index=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped["Case"] = relationship(back_populates="assignments")
    support_request: Mapped["SupportRequest"] = relationship(back_populates="assignments")
    assignee: Mapped["User"] = relationship(
        back_populates="assignments_received", foreign_keys=[assignee_user_id]
    )
    assigned_by: Mapped["User"] = relationship(
        back_populates="assignments_created", foreign_keys=[assigned_by_user_id]
    )

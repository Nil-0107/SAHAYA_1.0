"""Human support request model and lifecycle status."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin
from app.models.user import enum_column


class SupportRequestType(str, Enum):
    WELLBEING = "wellbeing"
    LEGAL = "legal"
    PROTECTION = "protection"


class SupportRequestStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class SupportRequest(DemoRecordMixin, Base):
    __tablename__ = "support_requests"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    type: Mapped[SupportRequestType] = mapped_column(
        enum_column(SupportRequestType, "support_request_type"), nullable=False, index=True
    )
    status: Mapped[SupportRequestStatus] = mapped_column(
        enum_column(SupportRequestStatus, "support_request_status"),
        nullable=False,
        default=SupportRequestStatus.PENDING,
        server_default=SupportRequestStatus.PENDING.value,
        index=True,
    )
    priority: Mapped[str] = mapped_column(String(40), nullable=False, default="standard", index=True)
    explicit_human_request: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(
        back_populates="support_requests", foreign_keys=[user_id]
    )
    case: Mapped["Case"] = relationship(back_populates="support_requests")
    assignments: Mapped[list["CaseAssignment"]] = relationship(back_populates="support_request")
    actions: Mapped[list["SupportAction"]] = relationship(back_populates="support_request")

"""Case model and case lifecycle status."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin
from app.models.user import enum_column


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Case(DemoRecordMixin, Base):
    __tablename__ = "cases"

    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    case_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    category_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[CaseStatus] = mapped_column(
        enum_column(CaseStatus, "case_status"),
        nullable=False,
        default=CaseStatus.OPEN,
        server_default=CaseStatus.OPEN.value,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    court_name: Mapped[str | None] = mapped_column(String(180))
    next_hearing: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    protection_request_open: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    wellbeing_review_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0", index=True
    )

    owner: Mapped["User"] = relationship(
        back_populates="owned_cases", foreign_keys=[owner_user_id]
    )
    documents: Mapped[list["CaseDocument"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    checkins: Mapped[list["Checkin"]] = relationship(back_populates="case")
    support_requests: Mapped[list["SupportRequest"]] = relationship(back_populates="case")
    assignments: Mapped[list["CaseAssignment"]] = relationship(back_populates="case")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="case")
    ai_conversations: Mapped[list["AIConversation"]] = relationship(back_populates="case")

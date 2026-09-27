"""Human support action model and action status."""

from enum import Enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin
from app.models.user import enum_column


class SupportActionStatus(str, Enum):
    RECORDED = "recorded"
    COMPLETED = "completed"
    FAILED = "failed"


class SupportAction(DemoRecordMixin, Base):
    __tablename__ = "support_actions"

    support_request_id: Mapped[int] = mapped_column(
        ForeignKey("support_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[SupportActionStatus] = mapped_column(
        enum_column(SupportActionStatus, "support_action_status"),
        nullable=False,
        default=SupportActionStatus.RECORDED,
        server_default=SupportActionStatus.RECORDED.value,
        index=True,
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False)

    support_request: Mapped["SupportRequest"] = relationship(back_populates="actions")
    actor: Mapped["User"] = relationship(
        back_populates="support_actions", foreign_keys=[actor_user_id]
    )

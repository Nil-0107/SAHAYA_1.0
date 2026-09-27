"""AI support conversation model and lifecycle status."""

from enum import Enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin
from app.models.user import enum_column


class AIConversationStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    UNAVAILABLE = "unavailable"


class AIConversation(DemoRecordMixin, Base):
    __tablename__ = "ai_conversations"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[int | None] = mapped_column(
        ForeignKey("cases.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[AIConversationStatus] = mapped_column(
        enum_column(AIConversationStatus, "ai_conversation_status"),
        nullable=False,
        default=AIConversationStatus.ACTIVE,
        server_default=AIConversationStatus.ACTIVE.value,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(160))

    user: Mapped["User"] = relationship(
        back_populates="ai_conversations", foreign_keys=[user_id]
    )
    case: Mapped["Case | None"] = relationship(back_populates="ai_conversations")
    messages: Mapped[list["AIMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

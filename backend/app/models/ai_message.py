"""AI support message model and delivery status."""

from enum import Enum

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin
from app.models.user import enum_column


class AIMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AIMessageStatus(str, Enum):
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"


class AIMessage(DemoRecordMixin, Base):
    __tablename__ = "ai_messages"

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[AIMessageRole] = mapped_column(
        enum_column(AIMessageRole, "ai_message_role"), nullable=False, index=True
    )
    status: Mapped[AIMessageStatus] = mapped_column(
        enum_column(AIMessageStatus, "ai_message_status"),
        nullable=False,
        default=AIMessageStatus.COMPLETE,
        server_default=AIMessageStatus.COMPLETE.value,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    conversation: Mapped["AIConversation"] = relationship(back_populates="messages")

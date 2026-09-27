"""Case document metadata and processing status."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin
from app.models.user import enum_column


class DocumentStatus(str, Enum):
    PENDING = "pending"
    STORED = "stored"
    PROCESSING = "processing"
    PROCESSED = "processed"
    REJECTED = "rejected"
    FAILED = "failed"


class CaseDocument(DemoRecordMixin, Base):
    __tablename__ = "case_documents"

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[DocumentStatus] = mapped_column(
        enum_column(DocumentStatus, "case_document_status"),
        nullable=False,
        default=DocumentStatus.STORED,
        server_default=DocumentStatus.STORED.value,
        index=True,
    )
    extracted_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped["Case"] = relationship(back_populates="documents")
    owner: Mapped["User"] = relationship(
        back_populates="owned_case_documents", foreign_keys=[owner_user_id]
    )

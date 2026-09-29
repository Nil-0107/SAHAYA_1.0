"""Well-being check-in and local-analysis status."""

from enum import Enum

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin
from app.models.user import enum_column


class CheckinAnalysisStatus(str, Enum):
    NOT_RUN = "not_run"
    COMPLETED = "completed"
    FAILED = "failed"


class Checkin(DemoRecordMixin, Base):
    __tablename__ = "checkins"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    case_id: Mapped[int | None] = mapped_column(
        ForeignKey("cases.id", ondelete="SET NULL"), index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_status: Mapped[CheckinAnalysisStatus] = mapped_column(
        enum_column(CheckinAnalysisStatus, "checkin_analysis_status"),
        nullable=False,
        default=CheckinAnalysisStatus.NOT_RUN,
        server_default=CheckinAnalysisStatus.NOT_RUN.value,
        index=True,
    )
    predicted_class: Mapped[int | None] = mapped_column(Integer)
    predicted_label: Mapped[str | None] = mapped_column(String(80))
    confidence: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str | None] = mapped_column(String(120), index=True)
    emotion_result: Mapped[dict | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="checkins", foreign_keys=[user_id])
    case: Mapped["Case | None"] = relationship(back_populates="checkins")

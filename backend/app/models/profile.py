"""User profile model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin


class Profile(DemoRecordMixin, Base):
    __tablename__ = "profiles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(40), nullable=False)
    city_or_district: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(120))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(20))
    safe_contact_method: Mapped[str | None] = mapped_column(String(80))
    address: Mapped[str | None] = mapped_column(String(255))
    case_reference: Mapped[str | None] = mapped_column(String(120))
    relationship_to_case: Mapped[str | None] = mapped_column(String(120))
    role_in_case: Mapped[str | None] = mapped_column(String(120))
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="profile")

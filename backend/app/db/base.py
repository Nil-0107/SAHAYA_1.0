"""Shared SQLAlchemy declarative base and demo provenance primitives."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DemoRecordMixin:
    """Provenance fields required on every SAHAYA database record.

    ``is_demo`` is data provenance only. Authentication and authorization code
    must never treat it as a credential, role grant, or production bypass.
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_demo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0", index=True
    )
    demo_key: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    @declared_attr
    def __table_args__(cls) -> tuple[CheckConstraint, ...]:
        return (
            CheckConstraint(
                "(is_demo = 0 AND demo_key IS NULL) "
                "OR (is_demo = 1 AND demo_key IS NOT NULL)",
                name=f"ck_{cls.__tablename__}_demo_marker",
            ),
        )

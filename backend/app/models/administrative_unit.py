"""Administrative geography used for backend scope enforcement."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DemoRecordMixin


class AdministrativeUnit(DemoRecordMixin, Base):
    __tablename__ = "administrative_units"

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    unit_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_units.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    parent: Mapped["AdministrativeUnit | None"] = relationship(
        back_populates="children", remote_side="AdministrativeUnit.id"
    )
    children: Mapped[list["AdministrativeUnit"]] = relationship(back_populates="parent")

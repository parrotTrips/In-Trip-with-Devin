"""Traveler progress tracking models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UpdatedAtMixin, UUIDPrimaryKeyMixin


class TravelerChecklistProgress(UUIDPrimaryKeyMixin, UpdatedAtMixin, Base):
    __tablename__ = "traveler_checklist_progress"
    __table_args__ = (
        UniqueConstraint("trip_traveler_id", "trip_phase_checklist_item_id"),
    )

    trip_traveler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_travelers.id"),
        nullable=False,
    )
    trip_phase_checklist_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_phase_checklist_items.id"),
        nullable=False,
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TravelerPhaseProgress(UUIDPrimaryKeyMixin, UpdatedAtMixin, Base):
    __tablename__ = "traveler_phase_progress"
    __table_args__ = (UniqueConstraint("trip_traveler_id", "trip_phase_id"),)

    trip_traveler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_travelers.id"),
        nullable=False,
    )
    trip_phase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_phases.id"),
        nullable=False,
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

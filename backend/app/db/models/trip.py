"""Trip catalog and participation models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TripTraveler(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_travelers"
    __table_args__ = (UniqueConstraint("wetravel_trip_uuid", "user_id"),)

    wetravel_trip_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )


class TripPhase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_phases"

    wetravel_trip_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    parent_phase_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_phases.id"),
    )
    phase_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    subtitle: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(Text)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_locked_by_default: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False)


class TripPhaseChecklistItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_phase_checklist_items"

    trip_phase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_phases.id"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)


class TripPhaseLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_phase_links"

    trip_phase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_phases.id"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class TripActivity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_activities"

    trip_phase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_phases.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    activity_type: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    practical_info: Mapped[str | None] = mapped_column(Text)
    amount_brl: Mapped[float | None] = mapped_column(Numeric(12, 2))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

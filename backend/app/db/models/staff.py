"""Staff operational models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TripContact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_contacts"

    wetravel_trip_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TripStaff(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_staff"
    __table_args__ = (UniqueConstraint("wetravel_trip_uuid", "user_id"),)

    wetravel_trip_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    function: Mapped[str | None] = mapped_column(Text)


class StaffTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "staff_tasks"

    trip_phase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_phases.id"), nullable=False
    )
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    trip_activity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_activities.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class ActivityCheckin(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "activity_checkins"
    __table_args__ = (
        UniqueConstraint("trip_activity_id", "trip_traveler_id"),
        Index("ix_activity_checkins_trip_activity_id", "trip_activity_id"),
        Index("ix_activity_checkins_trip_traveler_id", "trip_traveler_id"),
    )

    trip_activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_activities.id"), nullable=False
    )
    trip_traveler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_travelers.id"), nullable=False
    )
    scanned_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )


class ActivityParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "activity_participants"
    __table_args__ = (
        UniqueConstraint("trip_activity_id", "trip_traveler_id"),
        Index("ix_activity_participants_trip_activity_id", "trip_activity_id"),
        Index("ix_activity_participants_trip_traveler_id", "trip_traveler_id"),
    )

    trip_activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_activities.id"), nullable=False
    )
    trip_traveler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_travelers.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)


class ActivityCheckinScanEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "activity_checkin_scan_events"
    __table_args__ = (
        Index("ix_activity_checkin_scan_events_trip_activity_id", "trip_activity_id"),
        Index("ix_activity_checkin_scan_events_trip_traveler_id", "trip_traveler_id"),
        Index("ix_activity_checkin_scan_events_scanned_by_user_id", "scanned_by_user_id"),
    )

    trip_activity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_activities.id"), nullable=True
    )
    trip_traveler_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_travelers.id"), nullable=True
    )
    scanned_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    raw_payload_hash: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

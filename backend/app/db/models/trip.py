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


class TravelerAppFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "traveler_app_feedback"

    trip_traveler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_travelers.id", ondelete="CASCADE"),
        nullable=False,
    )
    feedback: Mapped[str] = mapped_column(Text, nullable=False)


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
    address: Mapped[str | None] = mapped_column(Text)
    max_checkins: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amount_brl: Mapped[float | None] = mapped_column(Numeric(12, 2))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class TripEmergencyContact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_emergency_contacts"

    wetravel_trip_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TripRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_recommendations"

    wetravel_trip_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category: Mapped[str | None] = mapped_column(Text)
    neighborhood: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    highlight: Mapped[str | None] = mapped_column(Text)
    price_range: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 1))
    map_url: Mapped[str | None] = mapped_column(Text)
    emoji: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    whatsapp_url: Mapped[str | None] = mapped_column(Text)
    contact_label: Mapped[str | None] = mapped_column(Text)


class TripFaq(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_faqs"

    wetravel_trip_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TripCancellationPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_cancellation_policies"

    wetravel_trip_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TripSettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_settings"

    trip_uuid: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    mode: Mapped[str] = mapped_column(Text, nullable=False, default="pre-trip")
    ideal_pace_phase_id: Mapped[str | None] = mapped_column(Text)

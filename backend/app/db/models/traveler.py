"""Traveler-specific profile and product models."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TravelerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "traveler_profiles"

    trip_traveler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_travelers.id"),
        nullable=False,
        unique=True,
    )
    preferred_name: Mapped[str | None] = mapped_column(Text)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(Text)
    passport_first_name: Mapped[str | None] = mapped_column(Text)
    passport_last_name: Mapped[str | None] = mapped_column(Text)
    passport_country: Mapped[str | None] = mapped_column(Text)
    passport_number: Mapped[str | None] = mapped_column(Text)
    passport_issue_date: Mapped[date | None] = mapped_column(Date)
    passport_expiration_date: Mapped[date | None] = mapped_column(Date)
    dietary_restrictions_flag: Mapped[bool | None] = mapped_column(Boolean)
    dietary_restrictions_details: Mapped[str | None] = mapped_column(Text)
    seasickness_flag: Mapped[bool | None] = mapped_column(Boolean)
    plus_one_flag: Mapped[bool | None] = mapped_column(Boolean)
    plus_one_name: Mapped[str | None] = mapped_column(Text)
    plus_one_email: Mapped[str | None] = mapped_column(Text)
    needs_flight_help_flag: Mapped[bool | None] = mapped_column(Boolean)
    flight_help_details: Mapped[str | None] = mapped_column(Text)
    needs_travel_insurance_help_flag: Mapped[bool | None] = mapped_column(Boolean)
    unforgettable_trip_details: Mapped[str | None] = mapped_column(Text)


class TravelerProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "traveler_products"

    trip_traveler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_travelers.id"),
        nullable=False,
        unique=True,
    )
    package_name: Mapped[str | None] = mapped_column(Text)
    room_type: Mapped[str | None] = mapped_column(Text)
    amount_paid_usd: Mapped[float | None] = mapped_column(Numeric(12, 2))
    purchased_addons_summary: Mapped[str | None] = mapped_column(Text)
    service_agreement_media_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_assets.id"),
    )

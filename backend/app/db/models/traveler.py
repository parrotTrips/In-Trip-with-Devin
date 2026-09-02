"""Traveler profile model."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Text
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
    avatar_url: Mapped[str | None] = mapped_column(Text)
    visa_status: Mapped[str | None] = mapped_column(Text)
    arrival_date: Mapped[date | None] = mapped_column(Date)
    arrival_time: Mapped[str | None] = mapped_column(Text)
    arrival_flight: Mapped[str | None] = mapped_column(Text)
    departure_date: Mapped[date | None] = mapped_column(Date)
    departure_time: Mapped[str | None] = mapped_column(Text)
    departure_flight: Mapped[str | None] = mapped_column(Text)
    checked_bags: Mapped[str | None] = mapped_column(Text)
    travel_insurance_status: Mapped[str | None] = mapped_column(Text)
    travel_insurance_brazil_medical_coverage: Mapped[str | None] = mapped_column(Text)
    travel_insurance_provider: Mapped[str | None] = mapped_column(Text)
    travel_insurance_policy_number: Mapped[str | None] = mapped_column(Text)
    travel_insurance_notes: Mapped[str | None] = mapped_column(Text)
    roommate_status: Mapped[str | None] = mapped_column(Text)
    roommate_email: Mapped[str | None] = mapped_column(Text)
    room_configuration: Mapped[str | None] = mapped_column(Text)
    roommate_gender_preference: Mapped[str | None] = mapped_column(Text)
    extended_stay_help: Mapped[str | None] = mapped_column(Text)
    extended_stay_help_details: Mapped[str | None] = mapped_column(Text)
    early_check_in_preference: Mapped[str | None] = mapped_column(Text)
    emergency_contact: Mapped[str | None] = mapped_column(Text)
    instagram_handle: Mapped[str | None] = mapped_column(Text)
    trip_mood: Mapped[str | None] = mapped_column(Text)
    social_topic: Mapped[str | None] = mapped_column(Text)
    always_up_for: Mapped[str | None] = mapped_column(Text)
    home_address: Mapped[str | None] = mapped_column(Text)
    final_considerations: Mapped[str | None] = mapped_column(Text)

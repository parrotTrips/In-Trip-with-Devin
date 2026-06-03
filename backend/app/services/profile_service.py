"""Profile service functions."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.traveler import TravelerProfile
from app.db.models.trip import TripTraveler
from app.db.models.user import User

PROFILE_FIELD_DEFAULTS = {
    "preferred_name": None,
    "email": None,
    "dob": None,
    "gender": None,
    "transfer_platform": None,
    "package_option": None,
    "num_people": None,
    "usd_amount": None,
    "proof_of_transfer": None,
    "dietary_restrictions_yn": None,
    "dietary_restrictions_desc": None,
    "seasickness_yn": None,
    "first_name_passport": None,
    "last_name_passport": None,
    "passport_country": None,
    "passport_number": None,
    "passport_issue_date": None,
    "passport_expiration_date": None,
    "plus_one_yn": None,
    "plus_one_name": None,
    "plus_one_email": None,
    "intl_flights_help_yn": None,
    "intl_flights_help_details": None,
    "travel_insurance_help_yn": None,
    "unforgettable_trip_details": None,
    "receive_addon_updates": None,
    "esim_qr_image": None,
    "roommate_user_id": None,
    "arrival_date": None,
    "arrival_time": None,
    "arrival_flight": None,
    "departure_date": None,
    "departure_time": None,
    "departure_flight": None,
    "service_agreement_url": None,
}

SUPPORTED_UPDATE_FIELDS = {
    "preferred_name",
    "email",
    "dob",
    "gender",
    "dietary_restrictions_yn",
    "dietary_restrictions_desc",
    "seasickness_yn",
    "first_name_passport",
    "last_name_passport",
    "passport_country",
    "passport_number",
    "passport_issue_date",
    "passport_expiration_date",
    "plus_one_yn",
    "plus_one_name",
    "plus_one_email",
    "intl_flights_help_yn",
    "intl_flights_help_details",
    "travel_insurance_help_yn",
    "unforgettable_trip_details",
}


def _parse_uuid(value: str, detail: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=detail) from exc


async def _resolve_trip_traveler(
    user_id: str,
    session: AsyncSession,
    wetravel_trip_uuid: str | None = None,
) -> tuple[User, TripTraveler]:
    parsed_user_id = _parse_uuid(user_id, "User not found")

    user = await session.scalar(select(User).where(User.id == parsed_user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if wetravel_trip_uuid:
        trip_traveler = await session.scalar(
            select(TripTraveler).where(
                TripTraveler.user_id == parsed_user_id,
                TripTraveler.wetravel_trip_uuid == wetravel_trip_uuid,
            )
        )
    else:
        trip_traveler = await session.scalar(
            select(TripTraveler)
            .where(TripTraveler.user_id == parsed_user_id)
            .order_by(TripTraveler.created_at)
            .limit(1)
        )

    if not trip_traveler:
        raise HTTPException(status_code=404, detail="Traveler not found for trip")

    return user, trip_traveler


def _parse_optional_date(value: str | None, field_name: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid date format for field '{field_name}'. Expected YYYY-MM-DD, got: '{value}'",
        )


def _encode_optional_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _encode_yes_no(value: bool | None) -> str | None:
    if value is None:
        return None
    return "yes" if value else "no"


def _decode_yes_no(value: str | None, field_name: str) -> bool | None:
    if value is None:
        return None
    if value == "yes":
        return True
    if value == "no":
        return False
    raise HTTPException(
        status_code=422,
        detail=f"Invalid value for field '{field_name}'. Expected 'yes' or 'no', got: '{value}'",
    )


async def get_profile(
    user_id: str,
    trip_id: str | None,
    session: AsyncSession,
) -> dict:
    """Return one traveler profile together with the linked basic user data."""
    user, trip_traveler = await _resolve_trip_traveler(user_id, session, trip_id)
    wetravel_uuid = trip_traveler.wetravel_trip_uuid

    profile = await session.scalar(
        select(TravelerProfile).where(
            TravelerProfile.trip_traveler_id == trip_traveler.id
        )
    )

    # Read-only package/payment data from WeTravel view (production only — not in test DB)
    wetravel_row = None
    try:
        async with session.begin_nested():
            wetravel_result = await session.execute(
                text("""
                    SELECT htp.package_names, htp.addon_names, htp.paid_amount, htp.currency
                    FROM host_trip_participants htp
                    JOIN wetravel_participant_phones wpp
                        ON wpp.email = htp.participant_email
                        AND wpp.trip_uuid = htp.trip_uuid
                    WHERE wpp.phone = :phone AND wpp.trip_uuid = :trip_uuid
                    LIMIT 1
                """),
                {"phone": user.phone, "trip_uuid": wetravel_uuid},
            )
            wetravel_row = wetravel_result.mappings().first()
    except Exception:
        pass

    profile_dict = dict(PROFILE_FIELD_DEFAULTS)
    profile_dict["email"] = user.email

    if wetravel_row:
        profile_dict["package_option"] = wetravel_row["package_names"]
        profile_dict["proof_of_transfer"] = wetravel_row["addon_names"]
        paid = wetravel_row["paid_amount"]
        if paid is not None:
            profile_dict["usd_amount"] = float(paid) / 100

    if profile:
        profile_dict["preferred_name"] = profile.preferred_name
        profile_dict["dob"] = _encode_optional_date(profile.date_of_birth)
        profile_dict["gender"] = profile.gender
        profile_dict["dietary_restrictions_yn"] = _encode_yes_no(profile.dietary_restrictions_flag)
        profile_dict["dietary_restrictions_desc"] = profile.dietary_restrictions_details
        profile_dict["seasickness_yn"] = _encode_yes_no(profile.seasickness_flag)
        profile_dict["first_name_passport"] = profile.passport_first_name
        profile_dict["last_name_passport"] = profile.passport_last_name
        profile_dict["passport_country"] = profile.passport_country
        profile_dict["passport_number"] = profile.passport_number
        profile_dict["passport_issue_date"] = _encode_optional_date(profile.passport_issue_date)
        profile_dict["passport_expiration_date"] = _encode_optional_date(profile.passport_expiration_date)
        profile_dict["plus_one_yn"] = _encode_yes_no(profile.plus_one_flag)
        profile_dict["plus_one_name"] = profile.plus_one_name
        profile_dict["plus_one_email"] = profile.plus_one_email
        profile_dict["intl_flights_help_yn"] = _encode_yes_no(profile.needs_flight_help_flag)
        profile_dict["intl_flights_help_details"] = profile.flight_help_details
        profile_dict["travel_insurance_help_yn"] = _encode_yes_no(profile.needs_travel_insurance_help_flag)
        profile_dict["unforgettable_trip_details"] = profile.unforgettable_trip_details
        profile_dict["service_agreement_url"] = profile.service_agreement_url

    return {
        "user_id": user_id,
        "wetravel_trip_uuid": wetravel_uuid,
        "phone": user.phone,
        "name": user.full_name,
        "profile": profile_dict if (profile or wetravel_row) else None,
        "roommate": None,
    }


async def update_profile(
    user_id: str,
    trip_id: str | None,
    update: dict,
    session: AsyncSession,
) -> dict:
    """Create or update a traveler profile while preserving current responses."""
    user, trip_traveler = await _resolve_trip_traveler(user_id, session, trip_id)
    update_data = {key: value for key, value in update.items() if value is not None}
    if not update_data:
        return {"message": "No fields to update"}

    # Silently ignore read-only or unknown fields (e.g. WeTravel-managed fields
    # like transfer_platform, package_option sent by the frontend form).
    update_data = {k: v for k, v in update_data.items() if k in SUPPORTED_UPDATE_FIELDS}

    profile = await session.scalar(
        select(TravelerProfile).where(
            TravelerProfile.trip_traveler_id == trip_traveler.id
        )
    )

    if profile is None:
        profile = TravelerProfile(trip_traveler_id=trip_traveler.id)
        session.add(profile)

    # updated_fields tracks fields assigned in-memory; session.commit() is called at the end.
    # If commit raises, the exception propagates and this list is never returned.
    updated_fields: list[str] = []

    if "preferred_name" in update_data:
        profile.preferred_name = update_data["preferred_name"]
        user.full_name = update_data["preferred_name"]
        updated_fields.append("preferred_name")
    if "dob" in update_data:
        profile.date_of_birth = _parse_optional_date(update_data["dob"], "dob")
        updated_fields.append("dob")
    if "gender" in update_data:
        profile.gender = update_data["gender"]
        updated_fields.append("gender")
    if "dietary_restrictions_yn" in update_data:
        profile.dietary_restrictions_flag = _decode_yes_no(update_data["dietary_restrictions_yn"], "dietary_restrictions_yn")
        updated_fields.append("dietary_restrictions_yn")
    if "dietary_restrictions_desc" in update_data:
        profile.dietary_restrictions_details = update_data["dietary_restrictions_desc"]
        updated_fields.append("dietary_restrictions_desc")
    if "seasickness_yn" in update_data:
        profile.seasickness_flag = _decode_yes_no(update_data["seasickness_yn"], "seasickness_yn")
        updated_fields.append("seasickness_yn")
    if "first_name_passport" in update_data:
        profile.passport_first_name = update_data["first_name_passport"]
        updated_fields.append("first_name_passport")
    if "last_name_passport" in update_data:
        profile.passport_last_name = update_data["last_name_passport"]
        updated_fields.append("last_name_passport")
    if "passport_country" in update_data:
        profile.passport_country = update_data["passport_country"]
        updated_fields.append("passport_country")
    if "passport_number" in update_data:
        profile.passport_number = update_data["passport_number"]
        updated_fields.append("passport_number")
    if "passport_issue_date" in update_data:
        profile.passport_issue_date = _parse_optional_date(update_data["passport_issue_date"], "passport_issue_date")
        updated_fields.append("passport_issue_date")
    if "passport_expiration_date" in update_data:
        profile.passport_expiration_date = _parse_optional_date(update_data["passport_expiration_date"], "passport_expiration_date")
        updated_fields.append("passport_expiration_date")
    if "plus_one_yn" in update_data:
        profile.plus_one_flag = _decode_yes_no(update_data["plus_one_yn"], "plus_one_yn")
        updated_fields.append("plus_one_yn")
    if "plus_one_name" in update_data:
        profile.plus_one_name = update_data["plus_one_name"]
        updated_fields.append("plus_one_name")
    if "plus_one_email" in update_data:
        profile.plus_one_email = update_data["plus_one_email"]
        updated_fields.append("plus_one_email")
    if "intl_flights_help_yn" in update_data:
        profile.needs_flight_help_flag = _decode_yes_no(update_data["intl_flights_help_yn"], "intl_flights_help_yn")
        updated_fields.append("intl_flights_help_yn")
    if "intl_flights_help_details" in update_data:
        profile.flight_help_details = update_data["intl_flights_help_details"]
        updated_fields.append("intl_flights_help_details")
    if "travel_insurance_help_yn" in update_data:
        profile.needs_travel_insurance_help_flag = _decode_yes_no(update_data["travel_insurance_help_yn"], "travel_insurance_help_yn")
        updated_fields.append("travel_insurance_help_yn")
    if "unforgettable_trip_details" in update_data:
        profile.unforgettable_trip_details = update_data["unforgettable_trip_details"]
        updated_fields.append("unforgettable_trip_details")
    if "email" in update_data:
        user.email = update_data["email"]
        updated_fields.append("email")

    await session.commit()

    return {"message": "Profile updated", "updated_fields": updated_fields}


async def get_trip_travelers(trip_id: str, session: AsyncSession) -> dict:
    """List all travelers available for roommate selection in a trip."""
    rows = await session.execute(
        select(User)
        .join(TripTraveler, TripTraveler.user_id == User.id)
        .where(TripTraveler.wetravel_trip_uuid == trip_id)
        .order_by(User.phone)
    )
    users = rows.scalars().all()

    return {
        "trip_id": trip_id,
        "travelers": [
            {"id": str(user.id), "name": user.full_name, "phone": user.phone}
            for user in users
        ],
    }

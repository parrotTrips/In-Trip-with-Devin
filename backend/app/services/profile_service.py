"""Profile service functions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.traveler import TravelerProduct, TravelerProfile
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
    "package_option",
    "usd_amount",
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
    trip_id: str,
    session: AsyncSession,
) -> tuple[User, TripTraveler]:
    parsed_user_id = _parse_uuid(user_id, "User not found")
    parsed_trip_id = _parse_uuid(trip_id, "Trip not found")

    user = await session.scalar(select(User).where(User.id == parsed_user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    trip_traveler = await session.scalar(
        select(TripTraveler).where(
            TripTraveler.user_id == parsed_user_id,
            TripTraveler.trip_id == parsed_trip_id,
        )
    )
    if not trip_traveler:
        raise HTTPException(status_code=404, detail="Traveler not found for trip")

    return user, trip_traveler


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _encode_optional_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _encode_yes_no(value: bool | None) -> str | None:
    if value is None:
        return None
    return "yes" if value else "no"


def _decode_yes_no(value: str | None) -> bool | None:
    if value is None:
        return None
    if value == "yes":
        return True
    if value == "no":
        return False
    return None


async def get_profile(user_id: str, trip_id: str, session: AsyncSession) -> dict:
    """Return one traveler profile together with the linked basic user data."""
    user, trip_traveler = await _resolve_trip_traveler(user_id, trip_id, session)
    profile = await session.scalar(
        select(TravelerProfile).where(
            TravelerProfile.trip_traveler_id == trip_traveler.id
        )
    )
    product = await session.scalar(
        select(TravelerProduct).where(
            TravelerProduct.trip_traveler_id == trip_traveler.id
        )
    )

    if not profile and not product and user.email is None:
        return {
            "user_id": user_id,
            "trip_id": trip_id,
            "phone": user.phone,
            "name": user.full_name,
            "profile": None,
            "roommate": None,
        }

    profile_dict = dict(PROFILE_FIELD_DEFAULTS)
    profile_dict["preferred_name"] = profile.preferred_name if profile else None
    profile_dict["email"] = user.email
    profile_dict["dob"] = _encode_optional_date(profile.date_of_birth) if profile else None
    profile_dict["gender"] = profile.gender if profile else None
    profile_dict["package_option"] = product.package_name if product else None
    profile_dict["usd_amount"] = (
        float(product.amount_paid_usd)
        if product and product.amount_paid_usd is not None
        else None
    )
    profile_dict["dietary_restrictions_yn"] = (
        _encode_yes_no(profile.dietary_restrictions_flag) if profile else None
    )
    profile_dict["dietary_restrictions_desc"] = (
        profile.dietary_restrictions_details if profile else None
    )
    profile_dict["seasickness_yn"] = (
        _encode_yes_no(profile.seasickness_flag) if profile else None
    )
    profile_dict["first_name_passport"] = (
        profile.passport_first_name if profile else None
    )
    profile_dict["last_name_passport"] = profile.passport_last_name if profile else None
    profile_dict["passport_country"] = profile.passport_country if profile else None
    profile_dict["passport_number"] = profile.passport_number if profile else None
    profile_dict["passport_issue_date"] = (
        _encode_optional_date(profile.passport_issue_date) if profile else None
    )
    profile_dict["passport_expiration_date"] = (
        _encode_optional_date(profile.passport_expiration_date) if profile else None
    )
    profile_dict["plus_one_yn"] = _encode_yes_no(profile.plus_one_flag) if profile else None
    profile_dict["plus_one_name"] = profile.plus_one_name if profile else None
    profile_dict["plus_one_email"] = profile.plus_one_email if profile else None
    profile_dict["intl_flights_help_yn"] = (
        _encode_yes_no(profile.needs_flight_help_flag) if profile else None
    )
    profile_dict["intl_flights_help_details"] = (
        profile.flight_help_details if profile else None
    )
    profile_dict["travel_insurance_help_yn"] = (
        _encode_yes_no(profile.needs_travel_insurance_help_flag)
        if profile
        else None
    )
    profile_dict["unforgettable_trip_details"] = (
        profile.unforgettable_trip_details if profile else None
    )

    return {
        "user_id": user_id,
        "trip_id": trip_id,
        "phone": user.phone,
        "name": user.full_name,
        "profile": profile_dict,
        "roommate": None,
    }


async def update_profile(
    user_id: str,
    trip_id: str,
    update: dict,
    session: AsyncSession,
) -> dict:
    """Create or update a traveler profile while preserving current responses."""
    user, trip_traveler = await _resolve_trip_traveler(user_id, trip_id, session)
    update_data = {key: value for key, value in update.items() if value is not None}
    if not update_data:
        return {"message": "No fields to update"}

    unsupported_fields = sorted(set(update_data) - SUPPORTED_UPDATE_FIELDS)
    if unsupported_fields:
        raise HTTPException(
            status_code=400,
            detail={"unsupported_fields": unsupported_fields},
        )

    profile = await session.scalar(
        select(TravelerProfile).where(
            TravelerProfile.trip_traveler_id == trip_traveler.id
        )
    )
    product = await session.scalar(
        select(TravelerProduct).where(
            TravelerProduct.trip_traveler_id == trip_traveler.id
        )
    )

    profile_fields = {
        "preferred_name",
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
    product_fields = {"package_option", "usd_amount"}

    if profile is None and profile_fields.intersection(update_data):
        profile = TravelerProfile(trip_traveler_id=trip_traveler.id)
        session.add(profile)

    if product is None and product_fields.intersection(update_data):
        product = TravelerProduct(trip_traveler_id=trip_traveler.id)
        session.add(product)

    if profile is not None:
        if "preferred_name" in update_data:
            profile.preferred_name = update_data["preferred_name"]
            user.full_name = update_data["preferred_name"]
        if "dob" in update_data:
            profile.date_of_birth = _parse_optional_date(update_data["dob"])
        if "gender" in update_data:
            profile.gender = update_data["gender"]
        if "dietary_restrictions_yn" in update_data:
            profile.dietary_restrictions_flag = _decode_yes_no(
                update_data["dietary_restrictions_yn"]
            )
        if "dietary_restrictions_desc" in update_data:
            profile.dietary_restrictions_details = update_data[
                "dietary_restrictions_desc"
            ]
        if "seasickness_yn" in update_data:
            profile.seasickness_flag = _decode_yes_no(update_data["seasickness_yn"])
        if "first_name_passport" in update_data:
            profile.passport_first_name = update_data["first_name_passport"]
        if "last_name_passport" in update_data:
            profile.passport_last_name = update_data["last_name_passport"]
        if "passport_country" in update_data:
            profile.passport_country = update_data["passport_country"]
        if "passport_number" in update_data:
            profile.passport_number = update_data["passport_number"]
        if "passport_issue_date" in update_data:
            profile.passport_issue_date = _parse_optional_date(
                update_data["passport_issue_date"]
            )
        if "passport_expiration_date" in update_data:
            profile.passport_expiration_date = _parse_optional_date(
                update_data["passport_expiration_date"]
            )
        if "plus_one_yn" in update_data:
            profile.plus_one_flag = _decode_yes_no(update_data["plus_one_yn"])
        if "plus_one_name" in update_data:
            profile.plus_one_name = update_data["plus_one_name"]
        if "plus_one_email" in update_data:
            profile.plus_one_email = update_data["plus_one_email"]
        if "intl_flights_help_yn" in update_data:
            profile.needs_flight_help_flag = _decode_yes_no(
                update_data["intl_flights_help_yn"]
            )
        if "intl_flights_help_details" in update_data:
            profile.flight_help_details = update_data["intl_flights_help_details"]
        if "travel_insurance_help_yn" in update_data:
            profile.needs_travel_insurance_help_flag = _decode_yes_no(
                update_data["travel_insurance_help_yn"]
            )
        if "unforgettable_trip_details" in update_data:
            profile.unforgettable_trip_details = update_data[
                "unforgettable_trip_details"
            ]

    if "email" in update_data:
        user.email = update_data["email"]

    if product is not None:
        if "package_option" in update_data:
            product.package_name = update_data["package_option"]
        if "usd_amount" in update_data:
            product.amount_paid_usd = Decimal(str(update_data["usd_amount"]))

    await session.commit()

    return {"message": "Profile updated"}


async def get_trip_travelers(trip_id: str, session: AsyncSession) -> dict:
    """List all travelers available for roommate selection in a trip."""
    parsed_trip_id = _parse_uuid(trip_id, "Trip not found")
    rows = await session.execute(
        select(User)
        .join(TripTraveler, TripTraveler.user_id == User.id)
        .where(TripTraveler.trip_id == parsed_trip_id)
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

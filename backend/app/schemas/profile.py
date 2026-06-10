"""Profile registration schemas."""

from typing import Optional

from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    """Trip registration fields persisted for a traveler profile."""

    preferred_name: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    transfer_platform: Optional[str] = None
    package_option: Optional[str] = None
    num_people: Optional[int] = None
    usd_amount: Optional[float] = None
    proof_of_transfer: Optional[str] = None
    dietary_restrictions_yn: Optional[str] = None
    dietary_restrictions_desc: Optional[str] = None
    seasickness_yn: Optional[str] = None
    first_name_passport: Optional[str] = None
    last_name_passport: Optional[str] = None
    passport_country: Optional[str] = None
    passport_number: Optional[str] = None
    passport_issue_date: Optional[str] = None
    passport_expiration_date: Optional[str] = None
    plus_one_yn: Optional[str] = None
    plus_one_name: Optional[str] = None
    plus_one_email: Optional[str] = None
    intl_flights_help_yn: Optional[str] = None
    intl_flights_help_details: Optional[str] = None
    travel_insurance_help_yn: Optional[str] = None
    unforgettable_trip_details: Optional[str] = None
    receive_addon_updates: Optional[str] = None
    esim_qr_image: Optional[str] = None
    roommate_user_id: Optional[str] = None
    arrival_date: Optional[str] = None
    arrival_time: Optional[str] = None
    arrival_flight: Optional[str] = None
    departure_date: Optional[str] = None
    departure_time: Optional[str] = None
    departure_flight: Optional[str] = None

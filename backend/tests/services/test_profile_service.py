import asyncio
import sqlite3

from app.db.database import init_db
from app.services.profile_service import get_profile, update_profile


def seed_user(database_path, phone="+5511222222222", name=None):
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO users (phone, name) VALUES (?, ?)",
            (phone, name),
        )
        connection.commit()
        return cursor.lastrowid


def test_get_profile_returns_empty_profile_for_existing_user(tmp_path):
    database_path = tmp_path / "profile.db"
    asyncio.run(init_db(database_path))
    user_id = seed_user(database_path, name="Alice")

    response = asyncio.run(get_profile(user_id, database_path=database_path))

    assert response == {
        "user_id": user_id,
        "phone": "+5511222222222",
        "name": "Alice",
        "profile": None,
        "roommate": None,
    }


def test_update_profile_creates_profile_and_updates_user_name(tmp_path):
    database_path = tmp_path / "profile.db"
    asyncio.run(init_db(database_path))
    user_id = seed_user(database_path)

    update_response = asyncio.run(
        update_profile(
            user_id,
            {"preferred_name": "Carol", "email": "carol@example.com"},
            database_path=database_path,
        )
    )
    profile_response = asyncio.run(get_profile(user_id, database_path=database_path))

    assert update_response == {"message": "Profile updated"}
    assert profile_response == {
        "user_id": user_id,
        "phone": "+5511222222222",
        "name": "Carol",
        "profile": {
            "preferred_name": "Carol",
            "email": "carol@example.com",
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
        },
        "roommate": None,
    }

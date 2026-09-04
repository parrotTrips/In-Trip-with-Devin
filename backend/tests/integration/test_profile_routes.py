import asyncio
from datetime import date
from uuid import UUID

from sqlalchemy import text

from app.db.models.trip import TripTraveler

TEST_TRIP_UUID = "test_trip_001"


async def seed_trip_assignment(session_factory, *, user_id):
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": TEST_TRIP_UUID,
                "title": "Test Trip",
                "dest": "Brazil",
                "sd": date(2027, 7, 1),
                "ed": date(2027, 7, 10),
            },
        )
        session.add(TripTraveler(wetravel_trip_uuid=TEST_TRIP_UUID, user_id=UUID(user_id)))
        await session.commit()
        return TEST_TRIP_UUID


async def seed_synced_trip_assignment(
    session_factory,
    *,
    user_id: str,
    trip_uuid: str,
    start_date: date,
    end_date: date | None,
):
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
            ),
            {
                "uuid": trip_uuid,
                "title": "Ended Trip",
                "dest": "Brazil",
                "sd": start_date,
                "ed": end_date,
            },
        )
        session.add(TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=UUID(user_id)))
        await session.commit()
        return trip_uuid


def create_user(seeded_client, phone="+5511990000000"):
    otp_response = seeded_client.post("/auth/request-otp", json={"phone": phone})
    verify_response = seeded_client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    data = verify_response.json()
    return data["user_id"], data["access_token"]


def test_profile_routes_read_and_update_profile(seeded_client, session_factory):
    user_id, token = create_user(seeded_client)
    headers = {"Authorization": f"Bearer {token}"}
    trip_uuid = asyncio.run(seed_trip_assignment(session_factory, user_id=user_id))

    initial_response = seeded_client.get(f"/profile/{user_id}?trip_id={trip_uuid}", headers=headers)
    update_response = seeded_client.put(
        f"/profile/{user_id}?trip_id={trip_uuid}",
        json={
            "preferred_name": "Eva",
            "email": "eva@example.com",
        },
        headers=headers,
    )
    updated_response = seeded_client.get(f"/profile/{user_id}?trip_id={trip_uuid}", headers=headers)

    assert initial_response.status_code == 200
    assert initial_response.json()["profile"] is None
    assert update_response.status_code == 200
    assert update_response.json()["message"] == "Profile updated"
    assert set(update_response.json()["updated_fields"]) == {"preferred_name", "email"}
    assert updated_response.status_code == 200
    assert updated_response.json()["wetravel_trip_uuid"] == trip_uuid
    assert updated_response.json()["name"] == "Eva"
    assert updated_response.json()["profile"]["preferred_name"] == "Eva"
    assert updated_response.json()["profile"]["email"] == "eva@example.com"


def test_trip_travelers_route_scopes_roommate_selection_to_the_trip(
    seeded_client, session_factory
):
    user_1_id, token_1 = create_user(seeded_client, phone="+5511990000001")
    user_2_id, _ = create_user(seeded_client, phone="+5511990000002")
    headers = {"Authorization": f"Bearer {token_1}"}

    asyncio.run(seed_trip_assignment(session_factory, user_id=user_1_id))
    asyncio.run(seed_trip_assignment(session_factory, user_id=user_2_id))

    response = seeded_client.get(f"/trip/{TEST_TRIP_UUID}/travelers", headers=headers)

    assert response.status_code == 200
    assert response.json()["trip_id"] == TEST_TRIP_UUID
    traveler_phones = {t["phone"] for t in response.json()["travelers"]}
    assert "+5511990000001" in traveler_phones
    assert "+5511990000002" in traveler_phones


def test_profile_route_without_trip_id_ignores_ended_trip_assignment(seeded_client, session_factory):
    user_id, token = create_user(seeded_client, phone="+5511990000003")
    headers = {"Authorization": f"Bearer {token}"}
    asyncio.run(
        seed_synced_trip_assignment(
            session_factory,
            user_id=user_id,
            trip_uuid="profile-ended-trip",
            start_date=date(2000, 1, 1),
            end_date=date(2000, 1, 2),
        )
    )

    response = seeded_client.get(f"/profile/{user_id}", headers=headers)

    assert response.status_code == 404


def test_profile_route_ignores_unsupported_orphan_fields(seeded_client, session_factory):
    """Read-only WeTravel fields are silently ignored, not rejected with 400."""
    user_id, token = create_user(seeded_client, phone="+5511990000003")
    headers = {"Authorization": f"Bearer {token}"}
    trip_uuid = asyncio.run(seed_trip_assignment(session_factory, user_id=user_id))

    response = seeded_client.put(
        f"/profile/{user_id}?trip_id={trip_uuid}",
        json={
            "transfer_platform": "wise",
            "preferred_name": "Test",  # supported field mixed in
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Profile updated"
    assert response.json()["updated_fields"] == ["preferred_name"]


def test_profile_route_persists_pre_departure_information(seeded_client, session_factory):
    user_id, token = create_user(seeded_client, phone="+5511991000001")
    headers = {"Authorization": f"Bearer {token}"}
    trip_uuid = asyncio.run(seed_trip_assignment(session_factory, user_id=user_id))

    response = seeded_client.put(
        f"/profile/{user_id}?trip_id={trip_uuid}",
        json={
            "visa_status": "I am not sure and I need orientation about it",
            "arrival_date": "2026-10-03",
            "arrival_time": "14:30",
            "arrival_flight": "GRU, AA 1234",
            "departure_date": "2026-10-12",
            "departure_time": "21:45",
            "departure_flight": "GIG, LA 4567",
            "checked_bags": "No checked bags, I travel light",
            "travel_insurance_status": "Already hired one",
            "travel_insurance_brazil_medical_coverage": "Yes",
            "travel_insurance_provider": "SafetyWing",
            "travel_insurance_policy_number": "POL-123",
            "travel_insurance_notes": "Covers hiking.",
            "roommate_status": "I am staying in an individual room",
            "roommate_email": "",
            "room_configuration": "One double bed (for two people)",
            "roommate_gender_preference": "No preference",
            "extended_stay_help": "No, thanks",
            "extended_stay_help_details": "",
            "early_check_in_preference": "I’ll arrive after the check-in time.",
            "emergency_contact": "Maria +5511999999999",
            "instagram_handle": "@alice",
            "trip_mood": "I’m here for what’s local, unique, and off the beaten path.",
            "social_topic": "Brazilian food",
            "always_up_for": "Beach\nLive music",
            "home_address": "123 Main St",
            "final_considerations": "No duplicated registration fields here.",
        },
        headers=headers,
    )
    updated_response = seeded_client.get(f"/profile/{user_id}?trip_id={trip_uuid}", headers=headers)

    assert response.status_code == 200
    assert updated_response.status_code == 200
    profile = updated_response.json()["profile"]
    assert profile["visa_status"] == "I am not sure and I need orientation about it"
    assert profile["arrival_date"] == "2026-10-03"
    assert profile["departure_flight"] == "GIG, LA 4567"
    assert profile["travel_insurance_provider"] == "SafetyWing"
    assert profile["emergency_contact"] == "Maria +5511999999999"

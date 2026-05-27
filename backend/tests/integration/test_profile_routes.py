import asyncio
from uuid import UUID

from app.db.models.trip import TripTraveler

TEST_TRIP_UUID = "test_trip_001"


async def seed_trip_assignment(session_factory, *, user_id):
    async with session_factory() as session:
        session.add(TripTraveler(wetravel_trip_uuid=TEST_TRIP_UUID, user_id=UUID(user_id)))
        await session.commit()
        return TEST_TRIP_UUID


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
    assert update_response.json() == {"message": "Profile updated"}
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


def test_profile_route_rejects_unsupported_orphan_fields(seeded_client, session_factory):
    user_id, token = create_user(seeded_client, phone="+5511990000003")
    headers = {"Authorization": f"Bearer {token}"}
    trip_uuid = asyncio.run(seed_trip_assignment(session_factory, user_id=user_id))

    response = seeded_client.put(
        f"/profile/{user_id}?trip_id={trip_uuid}",
        json={
            "transfer_platform": "wise",
            "arrival_date": "2026-02-01",
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "unsupported_fields": ["arrival_date", "transfer_platform"]
        }
    }

import asyncio
from datetime import date
from uuid import UUID

from app.db.models.trip import Trip, TripTraveler


async def seed_trip_assignment(
    session_factory,
    *,
    user_id,
    trip_name="Ross 2026",
    short_name="ross26",
):
    async with session_factory() as session:
        trip = Trip(
            name=trip_name,
            short_name=short_name,
            description="Integration trip",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 7),
            status="published",
        )
        session.add(trip)
        await session.flush()
        session.add(TripTraveler(trip_id=trip.id, user_id=UUID(user_id)))
        await session.commit()
        return str(trip.id)


def create_user(client, phone="+5511990000000"):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    return verify_response.json()["user_id"]


def test_profile_routes_read_and_update_profile(client, session_factory):
    user_id = create_user(client)
    trip_id = asyncio.run(seed_trip_assignment(session_factory, user_id=user_id))

    initial_response = client.get(f"/profile/{user_id}?trip_id={trip_id}")
    update_response = client.put(
        f"/profile/{user_id}?trip_id={trip_id}",
        json={
            "preferred_name": "Eva",
            "email": "eva@example.com",
            "package_option": "Shared Room",
        },
    )
    updated_response = client.get(f"/profile/{user_id}?trip_id={trip_id}")

    assert initial_response.status_code == 200
    assert initial_response.json()["profile"] is None
    assert update_response.status_code == 200
    assert update_response.json() == {"message": "Profile updated"}
    assert updated_response.status_code == 200
    assert updated_response.json()["trip_id"] == trip_id
    assert updated_response.json()["name"] == "Eva"
    assert updated_response.json()["profile"]["preferred_name"] == "Eva"
    assert updated_response.json()["profile"]["email"] == "eva@example.com"
    assert updated_response.json()["profile"]["package_option"] == "Shared Room"


def test_trip_travelers_route_scopes_roommate_selection_to_the_trip(
    client, session_factory
):
    user_1_id = create_user(client, phone="+5511990000001")
    user_2_id = create_user(client, phone="+5511990000002")

    trip_id = asyncio.run(seed_trip_assignment(session_factory, user_id=user_1_id))
    asyncio.run(seed_trip_assignment(session_factory, user_id=user_2_id))

    response = client.get(f"/trip/{trip_id}/travelers")

    assert response.status_code == 200
    assert response.json() == {
        "trip_id": trip_id,
        "travelers": [
            {
                "id": user_1_id,
                "name": None,
                "phone": "+5511990000001",
            }
        ],
    }


def test_profile_route_rejects_unsupported_orphan_fields(client, session_factory):
    user_id = create_user(client, phone="+5511990000003")
    trip_id = asyncio.run(seed_trip_assignment(session_factory, user_id=user_id))

    response = client.put(
        f"/profile/{user_id}?trip_id={trip_id}",
        json={
            "transfer_platform": "wise",
            "arrival_date": "2026-02-01",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "unsupported_fields": ["arrival_date", "transfer_platform"]
        }
    }

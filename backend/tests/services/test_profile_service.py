import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.db.models.traveler import TravelerProfile
from app.db.models.trip import TripTraveler
from app.db.models.user import User
from app.services.profile_service import get_profile, get_trip_travelers, update_profile

TEST_TRIP_A = "test_profile_trip_A"
TEST_TRIP_B = "test_profile_trip_B"


async def seed_trip_assignment(
    session_factory,
    *,
    phone="+5511222222222",
    name=None,
    wetravel_trip_uuid=TEST_TRIP_A,
):
    async with session_factory() as session:
        user = User(phone=phone, full_name=name, status="active")
        session.add(user)
        await session.flush()

        trip_traveler = TripTraveler(wetravel_trip_uuid=wetravel_trip_uuid, user_id=user.id)
        session.add(trip_traveler)
        await session.commit()

        return {
            "user_id": str(user.id),
            "wetravel_trip_uuid": wetravel_trip_uuid,
            "trip_traveler_id": trip_traveler.id,
        }


def test_get_profile_returns_empty_profile_for_existing_trip_traveler(session_factory):
    async def run_test():
        seeded = await seed_trip_assignment(session_factory, name="Alice")

        async with session_factory() as session:
            response = await get_profile(seeded["user_id"], seeded["wetravel_trip_uuid"], session)

        assert response == {
            "user_id": seeded["user_id"],
            "wetravel_trip_uuid": seeded["wetravel_trip_uuid"],
            "phone": "+5511222222222",
            "name": "Alice",
            "profile": None,
            "roommate": None,
        }

    asyncio.run(run_test())


def test_update_profile_creates_profile_through_trip_traveler(session_factory):
    async def run_test():
        seeded = await seed_trip_assignment(session_factory)

        async with session_factory() as session:
            update_response = await update_profile(
                seeded["user_id"],
                seeded["wetravel_trip_uuid"],
                {
                    "preferred_name": "Carol",
                    "email": "carol@example.com",
                },
                session,
            )
            profile_response = await get_profile(
                seeded["user_id"], seeded["wetravel_trip_uuid"], session
            )
            profile_row = await session.scalar(
                select(TravelerProfile).where(
                    TravelerProfile.trip_traveler_id == seeded["trip_traveler_id"]
                )
            )

        assert update_response == {"message": "Profile updated"}
        assert profile_row is not None
        assert profile_row.preferred_name == "Carol"
        assert profile_response["name"] == "Carol"
        assert profile_response["profile"]["preferred_name"] == "Carol"
        assert profile_response["profile"]["email"] == "carol@example.com"

    asyncio.run(run_test())


def test_get_trip_travelers_returns_only_travelers_for_the_requested_trip(session_factory):
    async def run_test():
        primary = await seed_trip_assignment(
            session_factory,
            phone="+5511333333333",
            name="Ana",
            wetravel_trip_uuid=TEST_TRIP_A,
        )
        await seed_trip_assignment(
            session_factory,
            phone="+5511444444444",
            name="Bia",
            wetravel_trip_uuid=TEST_TRIP_B,
        )

        async with session_factory() as session:
            response = await get_trip_travelers(primary["wetravel_trip_uuid"], session)

        assert response == {
            "trip_id": primary["wetravel_trip_uuid"],
            "travelers": [
                {
                    "id": primary["user_id"],
                    "name": "Ana",
                    "phone": "+5511333333333",
                }
            ],
        }

    asyncio.run(run_test())


def test_update_profile_rejects_unsupported_orphan_fields(session_factory):
    async def run_test():
        seeded = await seed_trip_assignment(session_factory)

        async with session_factory() as session:
            with pytest.raises(HTTPException) as exc_info:
                await update_profile(
                    seeded["user_id"],
                    seeded["wetravel_trip_uuid"],
                    {
                        "transfer_platform": "wise",
                        "proof_of_transfer": "https://example.com/proof.png",
                    },
                    session,
                )

            profile_response = await get_profile(
                seeded["user_id"], seeded["wetravel_trip_uuid"], session
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == {
            "unsupported_fields": ["proof_of_transfer", "transfer_platform"]
        }
        assert profile_response["profile"] is None

    asyncio.run(run_test())

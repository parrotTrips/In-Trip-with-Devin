import asyncio
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.db.models.traveler import TravelerProduct, TravelerProfile
from app.db.models.trip import Trip, TripTraveler
from app.db.models.user import User
from app.services.profile_service import get_profile, get_trip_travelers, update_profile


async def seed_trip_assignment(
    session_factory,
    *,
    phone="+5511222222222",
    name=None,
    trip_name="Ross 2026",
    short_name="ross26",
):
    async with session_factory() as session:
        user = User(phone=phone, full_name=name, status="active")
        trip = Trip(
            name=trip_name,
            short_name=short_name,
            description="Test trip",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 7),
            status="published",
        )
        session.add_all([user, trip])
        await session.flush()

        trip_traveler = TripTraveler(trip_id=trip.id, user_id=user.id)
        session.add(trip_traveler)
        await session.commit()

        return {
            "user_id": str(user.id),
            "trip_id": str(trip.id),
            "trip_traveler_id": trip_traveler.id,
        }


def test_get_profile_returns_empty_profile_for_existing_trip_traveler(session_factory):
    async def run_test():
        seeded = await seed_trip_assignment(session_factory, name="Alice")

        async with session_factory() as session:
            response = await get_profile(seeded["user_id"], seeded["trip_id"], session)

        assert response == {
            "user_id": seeded["user_id"],
            "trip_id": seeded["trip_id"],
            "phone": "+5511222222222",
            "name": "Alice",
            "profile": None,
            "roommate": None,
        }

    asyncio.run(run_test())


def test_update_profile_creates_profile_and_product_through_trip_traveler(session_factory):
    async def run_test():
        seeded = await seed_trip_assignment(session_factory)

        async with session_factory() as session:
            update_response = await update_profile(
                seeded["user_id"],
                seeded["trip_id"],
                {
                    "preferred_name": "Carol",
                    "email": "carol@example.com",
                    "package_option": "Premium Cabin",
                    "usd_amount": 2999.5,
                },
                session,
            )
            profile_response = await get_profile(
                seeded["user_id"], seeded["trip_id"], session
            )
            profile_row = await session.scalar(
                select(TravelerProfile).where(
                    TravelerProfile.trip_traveler_id == seeded["trip_traveler_id"]
                )
            )
            product_row = await session.scalar(
                select(TravelerProduct).where(
                    TravelerProduct.trip_traveler_id == seeded["trip_traveler_id"]
                )
            )

        assert update_response == {"message": "Profile updated"}
        assert profile_row is not None
        assert product_row is not None
        assert profile_row.preferred_name == "Carol"
        assert product_row.package_name == "Premium Cabin"
        assert float(product_row.amount_paid_usd) == 2999.5
        assert profile_response["name"] == "Carol"
        assert profile_response["profile"]["preferred_name"] == "Carol"
        assert profile_response["profile"]["email"] == "carol@example.com"
        assert profile_response["profile"]["package_option"] == "Premium Cabin"
        assert profile_response["profile"]["usd_amount"] == 2999.5

    asyncio.run(run_test())


def test_get_trip_travelers_returns_only_travelers_for_the_requested_trip(session_factory):
    async def run_test():
        primary = await seed_trip_assignment(
            session_factory,
            phone="+5511333333333",
            name="Ana",
            trip_name="Ross 2026",
            short_name="ross26",
        )
        await seed_trip_assignment(
            session_factory,
            phone="+5511444444444",
            name="Bia",
            trip_name="Pantanal 2026",
            short_name="pantanal26",
        )

        async with session_factory() as session:
            response = await get_trip_travelers(primary["trip_id"], session)

        assert response == {
            "trip_id": primary["trip_id"],
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
                    seeded["trip_id"],
                    {
                        "transfer_platform": "wise",
                        "proof_of_transfer": "https://example.com/proof.png",
                    },
                    session,
                )

            profile_response = await get_profile(
                seeded["user_id"], seeded["trip_id"], session
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == {
            "unsupported_fields": ["proof_of_transfer", "transfer_platform"]
        }
        assert profile_response["profile"] is None

    asyncio.run(run_test())

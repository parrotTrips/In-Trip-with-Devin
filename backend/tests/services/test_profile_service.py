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


async def seed_profile_context(session_factory, *, phone="+5511999000000"):
    import uuid as _uuid_module
    trip_uuid = f"test_trip_{str(_uuid_module.uuid4())[:8]}"
    async with session_factory() as session:
        from app.db.models.user import User
        from app.db.models.trip import TripTraveler
        user = User(phone=phone, full_name="Test User", status="active")
        session.add(user)
        await session.flush()
        tt = TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=user.id)
        session.add(tt)
        await session.commit()
        return {"user": user, "trip_uuid": trip_uuid}


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

        assert update_response["message"] == "Profile updated"
        assert set(update_response["updated_fields"]) == {"preferred_name", "email"}
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


def test_update_profile_ignores_unsupported_orphan_fields(session_factory):
    """Read-only WeTravel fields are silently ignored, not rejected with 400."""
    async def run_test():
        seeded = await seed_trip_assignment(session_factory)

        async with session_factory() as session:
            result = await update_profile(
                seeded["user_id"],
                seeded["wetravel_trip_uuid"],
                {
                    "transfer_platform": "wise",
                    "proof_of_transfer": "https://example.com/proof.png",
                    "preferred_name": "Ana",  # this one IS supported
                },
                session,
            )

        # Unsupported fields are ignored, supported field is saved
        assert result["message"] == "Profile updated"
        assert result["updated_fields"] == ["preferred_name"]

    asyncio.run(run_test())


@pytest.mark.asyncio
async def test_update_profile_rejects_invalid_date_format(session_factory):
    """Invalid dob format returns 422, not 500."""
    ctx = await seed_profile_context(session_factory, phone="+5511000000010")
    async with session_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await update_profile(
                str(ctx["user"].id),
                ctx["trip_uuid"],
                {"dob": "not-a-date"},
                session,
            )
    assert exc_info.value.status_code == 422
    assert "dob" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_update_profile_rejects_invalid_yes_no_value(session_factory):
    """Invalid yes/no value returns 422 with field name in detail."""
    ctx = await seed_profile_context(session_factory, phone="+5511000000011")
    async with session_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await update_profile(
                str(ctx["user"].id),
                ctx["trip_uuid"],
                {"dietary_restrictions_yn": "maybe"},
                session,
            )
    assert exc_info.value.status_code == 422
    assert "dietary_restrictions_yn" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_update_profile_success_response_includes_updated_fields(session_factory):
    """Success response includes list of fields that were updated."""
    ctx = await seed_profile_context(session_factory, phone="+5511000000012")
    async with session_factory() as session:
        result = await update_profile(
            str(ctx["user"].id),
            ctx["trip_uuid"],
            {"preferred_name": "Lara", "gender": "female"},
            session,
        )
    assert result["message"] == "Profile updated"
    assert set(result["updated_fields"]) == {"preferred_name", "gender"}

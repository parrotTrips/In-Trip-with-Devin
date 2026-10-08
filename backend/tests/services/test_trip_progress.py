"""Per-traveler phase completion exposed by the trip phases API."""

import asyncio
import uuid
from datetime import date

from sqlalchemy import text

from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.trip import TripPhase, TripPhaseChecklistItem, TripTraveler
from app.db.models.user import User
from app.services.trip_service import get_trip_phases, get_trip_travelers, get_traveler_locations


async def _seed(session_factory, *, start_date=date(2099, 1, 1)):
    trip_uuid = f"test_progress_{uuid.uuid4().hex[:8]}"
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, 'Trip', 'Brazil', :sd, :ed)"
            ),
            {"uuid": trip_uuid, "sd": start_date, "ed": date(2099, 12, 31)},
        )
        user = User(phone=f"+55119{uuid.uuid4().int % 10**8:08d}", full_name="Ana", status="active")
        session.add(user)
        await session.flush()
        tt = TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=user.id)
        session.add(tt)

        phases = []
        for order in range(3):
            phase = TripPhase(
                wetravel_trip_uuid=trip_uuid,
                phase_type="pre-trip",
                title=f"Phase {order + 1}",
                short_description="",
                sort_order=order,
                is_locked_by_default=False,
                is_visible=True,
            )
            session.add(phase)
            phases.append(phase)
        await session.flush()

        required = TripPhaseChecklistItem(
            trip_phase_id=phases[2].id, label="Send passport", sort_order=0, is_required=True
        )
        optional = TripPhaseChecklistItem(
            trip_phase_id=phases[2].id, label="Optional extra", sort_order=1, is_required=False
        )
        session.add_all([required, optional])
        await session.flush()
        await session.commit()
        return {
            "trip_uuid": trip_uuid,
            "user_id": str(user.id),
            "tt_id": tt.id,
            "phase_ids": [str(p.id) for p in phases],
            "phases": phases,
            "required_item_id": required.id,
        }


def test_phase_completed_out_of_order_by_button_or_checklist(session_factory):
    async def run():
        seeded = await _seed(session_factory)
        async with session_factory() as session:
            # Phase 2 marked done with the button, phase 3 done through its checklist.
            session.add(TravelerPhaseProgress(
                trip_traveler_id=seeded["tt_id"],
                trip_phase_id=seeded["phases"][1].id,
                is_completed=True,
            ))
            session.add(TravelerChecklistProgress(
                trip_traveler_id=seeded["tt_id"],
                trip_phase_checklist_item_id=seeded["required_item_id"],
                is_completed=True,
            ))
            await session.commit()

            phases = await get_trip_phases(seeded["user_id"], seeded["trip_uuid"], session)
            travelers = await get_trip_travelers(seeded["user_id"], seeded["trip_uuid"], session)

        ids = seeded["phase_ids"]
        assert set(phases["completed_phase_ids"]) == {ids[1], ids[2]}
        assert phases["trip_mode"] == "pre-trip"
        # Phase 1 is still pending, so the traveler stays there.
        assert travelers["travelers"][0]["current_phase_id"] == ids[0]

    asyncio.run(run())


def test_staff_sees_pending_pre_trip_before_departure(session_factory):
    async def run():
        seeded = await _seed(session_factory)
        async with session_factory() as session:
            result = await get_traveler_locations(seeded["trip_uuid"], session)

        assert result["trip_mode"] == "pre-trip"
        [traveler] = result["travelers"]
        assert traveler["pending_pre_trip"] == 3

    asyncio.run(run())


def test_trip_switches_to_in_trip_on_start_date(session_factory):
    async def run():
        seeded = await _seed(session_factory, start_date=date(2020, 1, 1))
        async with session_factory() as session:
            phases = await get_trip_phases(seeded["user_id"], seeded["trip_uuid"], session)
        assert phases["trip_mode"] == "in-trip"
        assert phases["completed_phase_ids"] == []

    asyncio.run(run())


def test_staff_sees_each_traveler_position_pending_items_and_last_checkin(session_factory):
    from datetime import UTC, datetime

    from app.db.models.staff import ActivityCheckin
    from app.db.models.trip import TripActivity
    from app.services.trip_service import get_traveler_locations

    async def run():
        seeded = await _seed(session_factory, start_date=date(2020, 1, 1))
        async with session_factory() as session:
            day = TripPhase(
                wetravel_trip_uuid=seeded["trip_uuid"],
                phase_type="in-trip",
                title="Day 1",
                subtitle="Rio",
                short_description="",
                sort_order=10,
                starts_at=datetime(2020, 1, 1, 3, tzinfo=UTC),
                is_locked_by_default=False,
                is_visible=True,
            )
            session.add(day)
            await session.flush()
            activity = TripActivity(
                trip_phase_id=day.id,
                name="Boat tour",
                activity_type="included",
                short_description="",
                sort_order=0,
            )
            session.add(activity)
            await session.flush()
            session.add(TravelerPhaseProgress(
                trip_traveler_id=seeded["tt_id"],
                trip_phase_id=seeded["phases"][0].id,
                is_completed=True,
            ))
            session.add(ActivityCheckin(
                trip_activity_id=activity.id,
                trip_traveler_id=seeded["tt_id"],
                scanned_by_user_id=uuid.UUID(seeded["user_id"]),
                scan_number=1,
                checked_in_at=datetime(2020, 1, 1, 15, tzinfo=UTC),
            ))
            await session.commit()

            result = await get_traveler_locations(seeded["trip_uuid"], session)

        assert result["trip_mode"] == "in-trip"
        [traveler] = result["travelers"]
        assert traveler["name"] == "Ana"
        assert traveler["current_phase"] == {
            "id": str(day.id), "title": "Day 1", "subtitle": "Rio", "phase_type": "in-trip",
        }
        # Phases 2 and 3 of the pre-trip are still open.
        assert traveler["pending_pre_trip"] == 2
        assert traveler["last_checkin"]["activity_name"] == "Boat tour"
        assert traveler["last_checkin"]["day_title"] == "Day 1"

    asyncio.run(run())


def _shift_trip(session_factory, trip_uuid, *, start, end):
    async def run():
        async with session_factory() as session:
            await session.execute(
                text("UPDATE wetravel_trips SET start_date = :s, end_date = :e WHERE trip_uuid = :u"),
                {"s": start, "e": end, "u": trip_uuid},
            )
            await session.commit()
    return run()


def test_travelers_keep_access_for_14_days_after_the_trip(session_factory):
    from datetime import timedelta

    import pytest
    from fastapi import HTTPException

    from app.services.trip_membership_service import list_eligible_trips

    async def run():
        today = date.today()
        seeded = await _seed(session_factory)
        await _shift_trip(session_factory, seeded["trip_uuid"], start=today - timedelta(days=20), end=today - timedelta(days=13))
        async with session_factory() as session:
            await get_trip_phases(seeded["user_id"], seeded["trip_uuid"], session)
            trips = await list_eligible_trips(seeded["user_id"], session)
        assert [t["trip_id"] for t in trips] == [seeded["trip_uuid"]]

        await _shift_trip(session_factory, seeded["trip_uuid"], start=today - timedelta(days=25), end=today - timedelta(days=16))
        async with session_factory() as session:
            with pytest.raises(HTTPException) as exc:
                await get_trip_phases(seeded["user_id"], seeded["trip_uuid"], session)
            trips = await list_eligible_trips(seeded["user_id"], session)
        assert exc.value.status_code == 403
        assert trips == []

    asyncio.run(run())


def test_wrap_up_phase_is_listed_after_the_trip_days(session_factory):
    async def run():
        seeded = await _seed(session_factory)
        async with session_factory() as session:
            session.add(TripPhase(
                wetravel_trip_uuid=seeded["trip_uuid"],
                phase_type="post-trip",
                title="Trip Wrap-up",
                short_description="",
                sort_order=0,
                is_locked_by_default=False,
                is_visible=True,
            ))
            await session.commit()
            phases = await get_trip_phases(seeded["user_id"], seeded["trip_uuid"], session)
        assert [p["phase_type"] for p in phases["phases"]][-1] == "post-trip"

    asyncio.run(run())

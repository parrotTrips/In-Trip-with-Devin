"""Per-traveler phase completion exposed by the trip phases API."""

import asyncio
import uuid
from datetime import date

from sqlalchemy import text

from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.trip import TripPhase, TripPhaseChecklistItem, TripTraveler
from app.db.models.user import User
from app.services.trip_service import get_trip_phases, get_trip_travelers


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


def test_trip_switches_to_in_trip_on_start_date(session_factory):
    async def run():
        seeded = await _seed(session_factory, start_date=date(2020, 1, 1))
        async with session_factory() as session:
            phases = await get_trip_phases(seeded["user_id"], seeded["trip_uuid"], session)
        assert phases["trip_mode"] == "in-trip"
        assert phases["completed_phase_ids"] == []

    asyncio.run(run())

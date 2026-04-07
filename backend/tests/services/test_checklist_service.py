import asyncio
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.trip import Trip, TripPhase, TripPhaseChecklistItem, TripTraveler
from app.db.models.user import User
from app.services.checklist_service import (
    get_checklist_progress,
    get_phase_completions,
    update_checklist_item,
    update_phase_completion,
)


async def seed_checklist_context(session_factory, *, phone="+5511555555555"):
    async with session_factory() as session:
        user = User(phone=phone, full_name="Ana", status="active")
        trip = Trip(
            name="Ross 2026",
            short_name="ross26",
            description="Checklist test trip",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 7),
            status="published",
        )
        session.add_all([user, trip])
        await session.flush()

        trip_traveler = TripTraveler(trip_id=trip.id, user_id=user.id)
        session.add(trip_traveler)
        await session.flush()

        phase = TripPhase(
            trip_id=trip.id,
            phase_type="pre_trip",
            title="Before departure",
            subtitle=None,
            icon=None,
            short_description="Checklist",
            detailed_description=None,
            sort_order=1,
            starts_at=None,
            ends_at=None,
            is_locked_by_default=False,
            is_visible=True,
        )
        session.add(phase)
        await session.flush()

        passport_item = TripPhaseChecklistItem(
            trip_phase_id=phase.id,
            label="Passport",
            description=None,
            sort_order=1,
            is_required=True,
        )
        insurance_item = TripPhaseChecklistItem(
            trip_phase_id=phase.id,
            label="Insurance",
            description=None,
            sort_order=2,
            is_required=False,
        )
        session.add_all([passport_item, insurance_item])
        await session.commit()

        return {
            "user_id": str(user.id),
            "trip_id": str(trip.id),
            "trip_traveler_id": trip_traveler.id,
            "phase_id": str(phase.id),
            "passport_item_id": str(passport_item.id),
            "insurance_item_id": str(insurance_item.id),
        }


def test_checklist_progress_is_persisted_per_trip_traveler_and_item(session_factory):
    async def run_test():
        seeded = await seed_checklist_context(session_factory)

        async with session_factory() as session:
            await update_checklist_item(
                seeded["user_id"],
                {
                    "trip_id": seeded["trip_id"],
                    "phase_id": seeded["phase_id"],
                    "item_id": seeded["passport_item_id"],
                    "completed": True,
                },
                session,
            )
            await update_checklist_item(
                seeded["user_id"],
                {
                    "trip_id": seeded["trip_id"],
                    "phase_id": seeded["phase_id"],
                    "item_id": seeded["passport_item_id"],
                    "completed": False,
                },
                session,
            )
            await update_checklist_item(
                seeded["user_id"],
                {
                    "trip_id": seeded["trip_id"],
                    "phase_id": seeded["phase_id"],
                    "item_id": seeded["insurance_item_id"],
                    "completed": True,
                },
                session,
            )

            response = await get_checklist_progress(
                seeded["trip_id"], seeded["user_id"], session
            )
            row_count = await session.scalar(
                select(func.count())
                .select_from(TravelerChecklistProgress)
                .where(
                    TravelerChecklistProgress.trip_traveler_id
                    == seeded["trip_traveler_id"]
                )
            )

        assert row_count == 2
        assert response == {
            "trip_id": seeded["trip_id"],
            "user_id": seeded["user_id"],
            "progress": {
                seeded["phase_id"]: {
                    seeded["passport_item_id"]: False,
                    seeded["insurance_item_id"]: True,
                }
            },
        }

    asyncio.run(run_test())


def test_phase_completion_is_persisted_per_trip_traveler_and_phase(session_factory):
    async def run_test():
        seeded = await seed_checklist_context(session_factory)

        async with session_factory() as session:
            update_response = await update_phase_completion(
                seeded["user_id"],
                {
                    "trip_id": seeded["trip_id"],
                    "phase_id": seeded["phase_id"],
                    "completed": True,
                },
                session,
            )
            await update_phase_completion(
                seeded["user_id"],
                {
                    "trip_id": seeded["trip_id"],
                    "phase_id": seeded["phase_id"],
                    "completed": False,
                },
                session,
            )
            completions_response = await get_phase_completions(
                seeded["trip_id"], seeded["user_id"], session
            )
            row_count = await session.scalar(
                select(func.count())
                .select_from(TravelerPhaseProgress)
                .where(
                    TravelerPhaseProgress.trip_traveler_id == seeded["trip_traveler_id"]
                )
            )

        assert update_response == {"message": "Phase completion updated"}
        assert row_count == 1
        assert completions_response == {
            "trip_id": seeded["trip_id"],
            "user_id": seeded["user_id"],
            "completions": {seeded["phase_id"]: False},
        }

    asyncio.run(run_test())


def test_checklist_update_rejects_phase_and_item_from_another_trip(session_factory):
    async def run_test():
        seeded = await seed_checklist_context(session_factory)
        other_trip = await seed_checklist_context(
            session_factory,
            phone="+5511555555556",
        )

        async with session_factory() as session:
            with pytest.raises(HTTPException) as exc_info:
                await update_checklist_item(
                    seeded["user_id"],
                    {
                        "trip_id": seeded["trip_id"],
                        "phase_id": other_trip["phase_id"],
                        "item_id": other_trip["passport_item_id"],
                        "completed": True,
                    },
                    session,
                )

            row_count = await session.scalar(
                select(func.count()).select_from(TravelerChecklistProgress)
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Checklist item not found"
        assert row_count == 0

    asyncio.run(run_test())

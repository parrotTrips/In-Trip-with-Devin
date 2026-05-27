"""Checklist and phase completion service functions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.trip import TripPhase, TripPhaseChecklistItem, TripTraveler


def _parse_uuid(value: str, detail: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=detail) from exc


async def _resolve_trip_traveler(
    user_id: str,
    trip_id: str,
    session: AsyncSession,
) -> TripTraveler:
    trip_traveler = await session.scalar(
        select(TripTraveler).where(
            TripTraveler.user_id == _parse_uuid(user_id, "User not found"),
            TripTraveler.wetravel_trip_uuid == trip_id,
        )
    )
    if not trip_traveler:
        raise HTTPException(status_code=404, detail="Traveler not found for trip")
    return trip_traveler


async def update_checklist_item(
    user_id: str,
    update: dict,
    session: AsyncSession,
) -> dict:
    """Persist one checklist item completion state for a user."""
    trip_traveler = await _resolve_trip_traveler(user_id, update["trip_id"], session)
    phase_id = _parse_uuid(update["phase_id"], "Phase not found")
    item_id = _parse_uuid(update["item_id"], "Checklist item not found")

    checklist_item = await session.scalar(
        select(TripPhaseChecklistItem)
        .join(TripPhase, TripPhase.id == TripPhaseChecklistItem.trip_phase_id)
        .where(
            TripPhaseChecklistItem.id == item_id,
            TripPhaseChecklistItem.trip_phase_id == phase_id,
            TripPhase.wetravel_trip_uuid == update["trip_id"],
        )
    )
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    completed_at = datetime.now(UTC) if update["completed"] else None
    statement = insert(TravelerChecklistProgress).values(
        trip_traveler_id=trip_traveler.id,
        trip_phase_checklist_item_id=checklist_item.id,
        is_completed=update["completed"],
        completed_at=completed_at,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[
            TravelerChecklistProgress.trip_traveler_id,
            TravelerChecklistProgress.trip_phase_checklist_item_id,
        ],
        set_={
            "is_completed": statement.excluded.is_completed,
            "completed_at": statement.excluded.completed_at,
            "updated_at": datetime.now(UTC),
        },
    )
    await session.execute(statement)
    await session.commit()

    return {"message": "Checklist item updated"}


async def get_checklist_progress(
    trip_id: str,
    user_id: str,
    session: AsyncSession,
) -> dict:
    """Return all persisted checklist progress for one user and trip."""
    trip_traveler = await _resolve_trip_traveler(user_id, trip_id, session)
    rows = await session.execute(
        select(
            TravelerChecklistProgress,
            TripPhaseChecklistItem.trip_phase_id,
        )
        .join(
            TripPhaseChecklistItem,
            TripPhaseChecklistItem.id
            == TravelerChecklistProgress.trip_phase_checklist_item_id,
        )
        .where(TravelerChecklistProgress.trip_traveler_id == trip_traveler.id)
    )

    progress: dict[str, dict[str, bool]] = {}
    for progress_row, phase_id in rows.all():
        phase_key = str(phase_id)
        progress.setdefault(phase_key, {})[
            str(progress_row.trip_phase_checklist_item_id)
        ] = progress_row.is_completed

    return {"trip_id": trip_id, "user_id": user_id, "progress": progress}


async def update_phase_completion(
    user_id: str,
    update: dict,
    session: AsyncSession,
) -> dict:
    """Persist one phase completion state for a user."""
    trip_traveler = await _resolve_trip_traveler(user_id, update["trip_id"], session)
    phase = await session.scalar(
        select(TripPhase).where(
            TripPhase.id == _parse_uuid(update["phase_id"], "Phase not found"),
            TripPhase.wetravel_trip_uuid == update["trip_id"],
        )
    )
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    completed_at = datetime.now(UTC) if update["completed"] else None
    statement = insert(TravelerPhaseProgress).values(
        trip_traveler_id=trip_traveler.id,
        trip_phase_id=phase.id,
        is_completed=update["completed"],
        completed_at=completed_at,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[
            TravelerPhaseProgress.trip_traveler_id,
            TravelerPhaseProgress.trip_phase_id,
        ],
        set_={
            "is_completed": statement.excluded.is_completed,
            "completed_at": statement.excluded.completed_at,
            "updated_at": datetime.now(UTC),
        },
    )
    await session.execute(statement)
    await session.commit()

    return {"message": "Phase completion updated"}


async def get_phase_completions(
    trip_id: str,
    user_id: str,
    session: AsyncSession,
) -> dict:
    """Return all persisted phase completion states for one user and trip."""
    trip_traveler = await _resolve_trip_traveler(user_id, trip_id, session)
    rows = await session.scalars(
        select(TravelerPhaseProgress).where(
            TravelerPhaseProgress.trip_traveler_id == trip_traveler.id
        )
    )

    completions = {
        str(row.trip_phase_id): row.is_completed for row in rows.all()
    }
    return {"trip_id": trip_id, "user_id": user_id, "completions": completions}

"""Resolve eligible trip memberships and their per-trip roles."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.trip import TripTraveler


_ELIGIBLE_TRIPS_SQL = """
    SELECT
        wt.trip_uuid AS trip_id,
        wt.title,
        wt.destination,
        wt.start_date,
        wt.end_date,
        CASE WHEN ts.id IS NULL THEN 'traveler' ELSE 'staff' END AS role,
        CASE
            WHEN wt.start_date <= CURRENT_DATE
             AND (wt.end_date IS NULL OR wt.end_date >= CURRENT_DATE)
            THEN TRUE
            ELSE FALSE
        END AS is_current
    FROM trip_travelers tt
    JOIN wetravel_trips wt
      ON wt.trip_uuid = tt.wetravel_trip_uuid
    LEFT JOIN trip_staff ts
      ON ts.wetravel_trip_uuid = tt.wetravel_trip_uuid
     AND ts.user_id = tt.user_id
    WHERE tt.user_id = CAST(:user_id AS uuid)
      AND (wt.end_date IS NULL OR wt.end_date >= CURRENT_DATE)
      {trip_filter}
    ORDER BY
        CASE
            WHEN wt.start_date <= CURRENT_DATE
             AND (wt.end_date IS NULL OR wt.end_date >= CURRENT_DATE)
            THEN 0
            ELSE 1
        END,
        wt.start_date NULLS LAST
"""


def _eligible_trips_query(*, for_trip: bool = False):
    trip_filter = "AND wt.trip_uuid = :trip_id" if for_trip else ""
    return text(_ELIGIBLE_TRIPS_SQL.format(trip_filter=trip_filter))


async def list_eligible_trips(user_id: str, session: AsyncSession) -> list[dict]:
    """List a user's current and future trips in selection order."""
    result = await session.execute(_eligible_trips_query(), {"user_id": user_id})
    return [dict(row) for row in result.mappings().all()]


async def get_eligible_trip_membership(
    user_id: str, trip_id: str, session: AsyncSession
) -> dict | None:
    """Return one eligible membership, or ``None`` when it is unavailable."""
    result = await session.execute(
        _eligible_trips_query(for_trip=True),
        {"user_id": user_id, "trip_id": trip_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def require_trip_membership(
    user_id: str, trip_id: str, session: AsyncSession
) -> TripTraveler:
    """Return the exact trip membership, or 403 if the session was revoked.

    Unlike trip selection, authenticated endpoints do not apply current/future
    eligibility rules here; they only revalidate that the selected membership
    still exists.
    """
    try:
        parsed_user_id = UUID(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=403, detail="Trip membership required") from exc

    membership = await session.scalar(
        select(TripTraveler).where(
            TripTraveler.user_id == parsed_user_id,
            TripTraveler.wetravel_trip_uuid == trip_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Trip membership required")
    return membership

"""Resolve eligible trip memberships and their per-trip roles."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


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

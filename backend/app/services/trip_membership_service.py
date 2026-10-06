"""Resolve eligible trip memberships and their per-trip roles."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Date, Text, column, func, or_, select, table, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.trip import TripTraveler
from app.db.models.staff import TripStaff


_SAO_PAULO_TODAY_SQL = (
    "(CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date"
)
_START_DATE_SQL = "NULLIF(wt.start_date::text, '')::date"
_END_DATE_SQL = "NULLIF(wt.end_date::text, '')::date"

_ELIGIBLE_TRIPS_SQL = f"""
    SELECT
        wt.trip_uuid AS trip_id,
        wt.title,
        wt.destination,
        wt.start_date,
        wt.end_date,
        CASE WHEN ts.id IS NULL THEN 'traveler' ELSE 'staff' END AS role,
        CASE
            WHEN {_START_DATE_SQL} <= {_SAO_PAULO_TODAY_SQL}
             AND ({_END_DATE_SQL} IS NULL OR {_END_DATE_SQL} >= {_SAO_PAULO_TODAY_SQL})
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
      AND (
        ts.id IS NOT NULL
        OR {_END_DATE_SQL} IS NULL
        OR {_END_DATE_SQL} >= {_SAO_PAULO_TODAY_SQL}
      )
      {{trip_filter}}
    ORDER BY
        CASE
            WHEN {_START_DATE_SQL} <= {_SAO_PAULO_TODAY_SQL}
             AND ({_END_DATE_SQL} IS NULL OR {_END_DATE_SQL} >= {_SAO_PAULO_TODAY_SQL})
            THEN 0
            ELSE 1
        END,
        {_START_DATE_SQL} NULLS LAST
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
    """Return an eligible exact membership, or 403 when it is unavailable."""
    try:
        parsed_user_id = UUID(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=403, detail="Trip membership required") from exc

    wetravel_trips = table(
        "wetravel_trips",
        column("trip_uuid", Text),
        column("end_date", Text),
    )
    sao_paulo_today = func.timezone(
        "America/Sao_Paulo", func.current_timestamp()
    ).cast(Date)
    end_date = func.nullif(wetravel_trips.c.end_date.cast(Text), "").cast(Date)
    staff_membership_exists = (
        select(TripStaff.id)
        .where(
            TripStaff.user_id == parsed_user_id,
            TripStaff.wetravel_trip_uuid == trip_id,
        )
        .exists()
    )
    membership = await session.scalar(
        select(TripTraveler)
        .join(
            wetravel_trips,
            wetravel_trips.c.trip_uuid == TripTraveler.wetravel_trip_uuid,
        )
        .where(
            TripTraveler.user_id == parsed_user_id,
                TripTraveler.wetravel_trip_uuid == trip_id,
                or_(
                    staff_membership_exists,
                    end_date.is_(None),
                end_date >= sao_paulo_today,
            ),
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Trip membership required")
    return membership

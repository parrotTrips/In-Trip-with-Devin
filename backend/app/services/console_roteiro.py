"""Roteiro: in-trip days and the activities inside them.

Kept out of the generic section registry on purpose. That registry replaces a
whole list on every save, which is safe for flat lists with no dependants.
Activities have dependants — check-ins, participants, staff tasks and scan
events — so they are edited one by one, by id, and a delete that would take
attendance records with it is refused.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ACTIVITY_TYPES = ("included", "optional", "suggested", "logistics")

_ACTIVITY_FIELDS = (
    "name", "activity_type", "starts_at", "duration_minutes", "short_description",
    "practical_info", "address", "max_checkins", "amount_brl",
)
_REQUIRED = ("name", "activity_type")
_TIMESTAMPS = ("starts_at",)
_NUMBERS = {"duration_minutes": (0, None), "max_checkins": (1, None), "amount_brl": (0, None)}


def _clean(value: object) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _validate(data: dict, *, partial: bool) -> dict:
    """Return only known fields, checked. `partial` allows a PATCH to omit some."""
    fields = {k: _clean(v) for k, v in data.items() if k in _ACTIVITY_FIELDS}

    for key in _REQUIRED:
        if partial and key not in fields:
            continue
        if not fields.get(key):
            raise HTTPException(status_code=422, detail=f"'{key}' is required")

    if fields.get("activity_type") and fields["activity_type"] not in ACTIVITY_TYPES:
        allowed = ", ".join(ACTIVITY_TYPES)
        raise HTTPException(
            status_code=422, detail=f"'activity_type' must be one of: {allowed}"
        )

    for key, (minimum, maximum) in _NUMBERS.items():
        raw = fields.get(key)
        if raw is None:
            continue
        try:
            number = float(raw)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"'{key}' must be a number") from None
        if minimum is not None and number < minimum:
            raise HTTPException(status_code=422, detail=f"'{key}' must be at least {minimum}")
        if maximum is not None and number > maximum:
            raise HTTPException(status_code=422, detail=f"'{key}' must be at most {maximum}")
        fields[key] = number

    return fields


def _assignment(key: str) -> str:
    return f"{key} = CAST(:{key} AS timestamptz)" if key in _TIMESTAMPS else f"{key} = :{key}"


async def get_days(session: AsyncSession, trip_uuid: str) -> dict:
    """Return in-trip days with the activities of each."""
    day_rows = await session.execute(
        text("""
            SELECT id, title, subtitle, icon, short_description, detailed_description,
                   sort_order, is_visible, starts_at, ends_at
            FROM trip_phases
            WHERE wetravel_trip_uuid = :trip_uuid AND phase_type = 'in-trip'
            ORDER BY sort_order ASC
        """),
        {"trip_uuid": trip_uuid},
    )
    days = [dict(r._mapping) for r in day_rows]
    if not days:
        return {"days": []}

    activity_rows = await session.execute(
        text("""
            SELECT a.id, a.trip_phase_id, a.name, a.activity_type, a.starts_at,
                   a.duration_minutes, a.short_description, a.practical_info,
                   a.address, a.max_checkins, a.amount_brl, a.sort_order,
                   (SELECT count(*) FROM activity_checkins c
                     WHERE c.trip_activity_id = a.id) AS checkin_count,
                   (SELECT count(*) FROM activity_checkin_scan_events e
                     WHERE e.trip_activity_id = a.id) AS scan_count
            FROM trip_activities a
            JOIN trip_phases p ON p.id = a.trip_phase_id
            WHERE p.wetravel_trip_uuid = :trip_uuid AND p.phase_type = 'in-trip'
            ORDER BY a.sort_order ASC
        """),
        {"trip_uuid": trip_uuid},
    )
    by_day: dict = {}
    for row in activity_rows:
        activity = dict(row._mapping)
        phase_id = activity.pop("trip_phase_id")
        activity["id"] = str(activity["id"])
        by_day.setdefault(phase_id, []).append(activity)

    return {
        "days": [
            {
                **{k: (str(v) if k == "id" else v) for k, v in day.items()},
                "activities": by_day.get(day["id"], []),
            }
            for day in days
        ]
    }


async def create_activity(session: AsyncSession, day_id: str, data: dict) -> dict:
    """Append an activity to a day."""
    exists = await session.scalar(
        text("SELECT count(*) FROM trip_phases WHERE id = CAST(:p AS uuid)"), {"p": day_id}
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Day not found")

    fields = _validate(data, partial=False)
    fields.setdefault("short_description", "")
    fields.setdefault("practical_info", "")
    fields.setdefault("max_checkins", 1)

    next_order = await session.scalar(
        text("SELECT COALESCE(MAX(sort_order) + 1, 0) FROM trip_activities"
             " WHERE trip_phase_id = CAST(:p AS uuid)"),
        {"p": day_id},
    )
    columns = ", ".join(fields)
    values = ", ".join(
        f"CAST(:{k} AS timestamptz)" if k in _TIMESTAMPS else f":{k}" for k in fields
    )
    activity_id = await session.scalar(
        text(f"INSERT INTO trip_activities (id, trip_phase_id, {columns}, sort_order,"
             f" created_at, updated_at)"
             f" VALUES (gen_random_uuid(), CAST(:day_id AS uuid), {values}, :sort_order,"
             f"         now(), now()) RETURNING id"),
        {"day_id": day_id, "sort_order": next_order, **fields},
    )
    await session.commit()
    return {"id": str(activity_id)}


async def update_activity(session: AsyncSession, activity_id: str, data: dict) -> dict:
    """Update an activity in place, so its check-ins and scans survive."""
    fields = _validate(data, partial=True)
    if not fields:
        return {"id": activity_id, "updated": False}

    assignments = ", ".join(_assignment(k) for k in fields)
    result = await session.execute(
        text(f"UPDATE trip_activities SET {assignments}, updated_at = now()"
             f" WHERE id = CAST(:activity_id AS uuid)"),
        {"activity_id": activity_id, **fields},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    await session.commit()
    return {"id": activity_id, "updated": True}


async def delete_activity(session: AsyncSession, activity_id: str) -> dict:
    """Delete an activity, refusing when attendance records depend on it."""
    exists = await session.scalar(
        text("SELECT count(*) FROM trip_activities WHERE id = CAST(:a AS uuid)"),
        {"a": activity_id},
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Activity not found")

    checkins = await session.scalar(
        text("SELECT count(*) FROM activity_checkins WHERE trip_activity_id = CAST(:a AS uuid)"),
        {"a": activity_id},
    )
    scans = await session.scalar(
        text("SELECT count(*) FROM activity_checkin_scan_events"
             " WHERE trip_activity_id = CAST(:a AS uuid)"),
        {"a": activity_id},
    )
    if checkins or scans:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Activity has {checkins} check-in(s) and {scans} scan(s);"
                " deleting it would erase who attended"
            ),
        )

    await session.execute(
        text("DELETE FROM activity_participants WHERE trip_activity_id = CAST(:a AS uuid)"),
        {"a": activity_id},
    )
    await session.execute(
        text("DELETE FROM staff_tasks WHERE trip_activity_id = CAST(:a AS uuid)"),
        {"a": activity_id},
    )
    await session.execute(
        text("DELETE FROM trip_activities WHERE id = CAST(:a AS uuid)"), {"a": activity_id}
    )
    await session.commit()
    return {"id": activity_id, "deleted": True}


async def reorder_activities(
    session: AsyncSession, day_id: str, activity_ids: list[str]
) -> dict:
    """Set sort_order from each id's position in the list."""
    for index, activity_id in enumerate(activity_ids):
        await session.execute(
            text("UPDATE trip_activities SET sort_order = :sort_order, updated_at = now()"
                 " WHERE id = CAST(:activity_id AS uuid)"
                 "   AND trip_phase_id = CAST(:day_id AS uuid)"),
            {"sort_order": index, "activity_id": activity_id, "day_id": day_id},
        )
    await session.commit()
    return {"count": len(activity_ids)}

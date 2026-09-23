"""Console service: admin-authenticated trip content editing.

Separate from admin_service on purpose: the /admin prefix is public (see
_PUBLIC_PREFIXES in app/middleware/auth.py) because the Apps Script menu calls
it without a token. Everything here sits behind the JWT middleware and also
requires role=admin.
"""

from __future__ import annotations

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def require_admin(request: Request, session: AsyncSession) -> str:
    """Return the caller's user_id, or raise 403 if they are not an admin."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    role = await session.scalar(
        text("SELECT role FROM users WHERE id = CAST(:user_id AS uuid)"),
        {"user_id": user_id},
    )
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return str(user_id)


async def list_trips(session: AsyncSession) -> dict:
    """Return active trips (end_date today or later, or null)."""
    rows = await session.execute(
        text("""
            SELECT w.trip_uuid, w.title, w.destination, w.start_date, w.end_date,
                   (SELECT count(*) FROM trip_travelers t
                     WHERE t.wetravel_trip_uuid = w.trip_uuid) AS traveler_count,
                   (SELECT s.mode FROM trip_settings s
                     WHERE s.trip_uuid = w.trip_uuid) AS mode
            FROM wetravel_trips w
            WHERE w.end_date IS NULL OR w.end_date::date >= CURRENT_DATE
            ORDER BY w.start_date ASC
        """)
    )
    return {
        "trips": [
            {
                "trip_uuid": r.trip_uuid,
                "title": r.title,
                "destination": r.destination,
                "start_date": str(r.start_date) if r.start_date else None,
                "end_date": str(r.end_date) if r.end_date else None,
                "traveler_count": r.traveler_count or 0,
                "mode": r.mode,
            }
            for r in rows
        ]
    }


async def get_phases(
    session: AsyncSession, trip_uuid: str, phase_type: str = "pre-trip"
) -> dict:
    """Return phases of one type with their checklist items and links."""
    phase_rows = await session.execute(
        text("""
            SELECT id, title, subtitle, icon, short_description,
                   detailed_description, sort_order, is_visible,
                   starts_at, ends_at
            FROM trip_phases
            WHERE wetravel_trip_uuid = :trip_uuid AND phase_type = :phase_type
            ORDER BY sort_order ASC
        """),
        {"trip_uuid": trip_uuid, "phase_type": phase_type},
    )
    phases = [dict(r._mapping) for r in phase_rows]
    if not phases:
        return {"phases": []}

    # JOIN instead of passing the id list: ANY(:ids) inside text() relies on array
    # type inference and is brittle; joining on trip_uuid is equivalent and safe.
    checklist_rows = await session.execute(
        text("""
            SELECT i.id, i.trip_phase_id, i.label, i.is_required, i.sort_order
            FROM trip_phase_checklist_items i
            JOIN trip_phases p ON p.id = i.trip_phase_id
            WHERE p.wetravel_trip_uuid = :trip_uuid AND p.phase_type = :phase_type
            ORDER BY i.sort_order ASC
        """),
        {"trip_uuid": trip_uuid, "phase_type": phase_type},
    )
    link_rows = await session.execute(
        text("""
            SELECT l.id, l.trip_phase_id, l.label, l.url, l.sort_order
            FROM trip_phase_links l
            JOIN trip_phases p ON p.id = l.trip_phase_id
            WHERE p.wetravel_trip_uuid = :trip_uuid AND p.phase_type = :phase_type
            ORDER BY l.sort_order ASC
        """),
        {"trip_uuid": trip_uuid, "phase_type": phase_type},
    )

    by_phase_checklist: dict = {}
    for r in checklist_rows:
        by_phase_checklist.setdefault(r.trip_phase_id, []).append({
            "id": str(r.id), "label": r.label,
            "is_required": r.is_required, "sort_order": r.sort_order,
        })
    by_phase_links: dict = {}
    for r in link_rows:
        by_phase_links.setdefault(r.trip_phase_id, []).append({
            "id": str(r.id), "label": r.label,
            "url": r.url, "sort_order": r.sort_order,
        })

    return {
        "phases": [
            {
                **{k: (str(v) if k == "id" else v) for k, v in p.items()},
                "checklist": by_phase_checklist.get(p["id"], []),
                "links": by_phase_links.get(p["id"], []),
            }
            for p in phases
        ]
    }


async def create_phase(
    session: AsyncSession, trip_uuid: str, data: dict, phase_type: str = "pre-trip"
) -> dict:
    """Create a phase in draft state, appended at the end."""
    next_order = await session.scalar(
        text("""
            SELECT COALESCE(MAX(sort_order) + 1, 0) FROM trip_phases
            WHERE wetravel_trip_uuid = :trip_uuid AND phase_type = :phase_type
        """),
        {"trip_uuid": trip_uuid, "phase_type": phase_type},
    )
    phase_id = await session.scalar(
        text("""
            INSERT INTO trip_phases
                (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                 short_description, detailed_description, sort_order,
                 is_locked_by_default, is_visible, created_at, updated_at)
            VALUES (gen_random_uuid(), :trip_uuid, :phase_type, :title, :subtitle, :icon,
                    :short_description, :detailed_description, :sort_order,
                    false, false, now(), now())
            RETURNING id
        """),
        {"trip_uuid": trip_uuid, "phase_type": phase_type,
         "sort_order": next_order, **data},
    )
    await session.commit()
    return {"id": str(phase_id), "is_visible": False}


# Columns that are NOT NULL in the database: a null sent for these is ignored
# rather than allowed to hit a constraint violation.
_PHASE_REQUIRED = ("title", "short_description")
# Nullable columns: sending null clears them, which is how a date is removed.
_PHASE_NULLABLE = ("subtitle", "icon", "detailed_description", "starts_at", "ends_at")
_PHASE_TIMESTAMPS = ("starts_at", "ends_at")


async def update_phase(session: AsyncSession, phase_id: str, data: dict) -> dict:
    """Update only the fields explicitly provided.

    `data` comes from model_dump(exclude_unset=True), so a key being present means
    the caller sent it — including when the value is null.
    """
    fields = {
        k: v for k, v in data.items()
        if (k in _PHASE_REQUIRED and v is not None) or k in _PHASE_NULLABLE
    }
    if not fields:
        return {"id": phase_id, "updated": False}

    assignments = ", ".join(
        f"{k} = CAST(:{k} AS timestamptz)" if k in _PHASE_TIMESTAMPS else f"{k} = :{k}"
        for k in fields
    )
    result = await session.execute(
        text(f"UPDATE trip_phases SET {assignments}, updated_at = now() "
             f"WHERE id = CAST(:phase_id AS uuid)"),
        {"phase_id": phase_id, **fields},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Phase not found")
    await session.commit()
    return {"id": phase_id, "updated": True}


async def set_phase_visibility(session: AsyncSession, phase_id: str, is_visible: bool) -> dict:
    """Publish (visible) or unpublish (draft) a phase."""
    result = await session.execute(
        text("UPDATE trip_phases SET is_visible = :is_visible, updated_at = now() "
             "WHERE id = CAST(:phase_id AS uuid)"),
        {"phase_id": phase_id, "is_visible": is_visible},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Phase not found")
    await session.commit()
    return {"id": phase_id, "is_visible": is_visible}


async def delete_phase(session: AsyncSession, phase_id: str) -> dict:
    """Delete a phase and its children. Refuse if activities hang off it."""
    exists = await session.scalar(
        text("SELECT count(*) FROM trip_phases WHERE id = CAST(:p AS uuid)"), {"p": phase_id}
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Phase not found")

    # Pre-trip phases carry no activities today, but nothing in the schema forbids
    # it. Refusing beats hitting the foreign key violation that motivated this work.
    activity_count = await session.scalar(
        text("SELECT count(*) FROM trip_activities WHERE trip_phase_id = CAST(:p AS uuid)"),
        {"p": phase_id},
    )
    if activity_count:
        raise HTTPException(
            status_code=409,
            detail=f"Phase has {activity_count} activity(ies); delete them first",
        )

    await session.execute(
        text("""
            DELETE FROM traveler_checklist_progress
            WHERE trip_phase_checklist_item_id IN (
                SELECT id FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)
            )
        """),
        {"p": phase_id},
    )
    for stmt in (
        "DELETE FROM traveler_phase_progress WHERE trip_phase_id = CAST(:p AS uuid)",
        "DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)",
        "DELETE FROM trip_phase_links WHERE trip_phase_id = CAST(:p AS uuid)",
        "DELETE FROM trip_phases WHERE id = CAST(:p AS uuid)",
    ):
        await session.execute(text(stmt), {"p": phase_id})

    await session.commit()
    return {"id": phase_id, "deleted": True}


async def replace_checklist(session: AsyncSession, phase_id: str, items: list[dict]) -> dict:
    """Replace every checklist item of the phase; list position becomes sort_order."""
    await session.execute(
        text("""
            DELETE FROM traveler_checklist_progress
            WHERE trip_phase_checklist_item_id IN (
                SELECT id FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)
            )
        """),
        {"p": phase_id},
    )
    await session.execute(
        text("DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)"),
        {"p": phase_id},
    )
    for index, item in enumerate(items):
        await session.execute(
            text("""
                INSERT INTO trip_phase_checklist_items
                    (id, trip_phase_id, label, sort_order, is_required, created_at, updated_at)
                VALUES (gen_random_uuid(), CAST(:p AS uuid), :label, :sort_order, :is_required,
                        now(), now())
            """),
            {"p": phase_id, "label": item["label"],
             "sort_order": index, "is_required": item["is_required"]},
        )
    await session.commit()
    return {"count": len(items)}


async def replace_links(session: AsyncSession, phase_id: str, links: list[dict]) -> dict:
    """Replace every link of the phase; list position becomes sort_order."""
    await session.execute(
        text("DELETE FROM trip_phase_links WHERE trip_phase_id = CAST(:p AS uuid)"),
        {"p": phase_id},
    )
    for index, link in enumerate(links):
        await session.execute(
            text("""
                INSERT INTO trip_phase_links
                    (id, trip_phase_id, label, url, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), CAST(:p AS uuid), :label, :url, :sort_order,
                        now(), now())
            """),
            {"p": phase_id, "label": link["label"], "url": link["url"], "sort_order": index},
        )
    await session.commit()
    return {"count": len(links)}


async def reorder_phases(session: AsyncSession, trip_uuid: str, phase_ids: list[str]) -> dict:
    """Set sort_order from the position of each id in the list."""
    for index, phase_id in enumerate(phase_ids):
        await session.execute(
            text("""
                UPDATE trip_phases SET sort_order = :sort_order, updated_at = now()
                WHERE id = CAST(:phase_id AS uuid) AND wetravel_trip_uuid = :trip_uuid
            """),
            {"sort_order": index, "phase_id": phase_id, "trip_uuid": trip_uuid},
        )
    await session.commit()
    return {"count": len(phase_ids)}

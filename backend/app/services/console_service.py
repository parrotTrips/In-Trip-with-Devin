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
            SELECT trip_uuid, title, start_date, end_date
            FROM wetravel_trips
            WHERE end_date IS NULL OR end_date::date >= CURRENT_DATE
            ORDER BY start_date ASC
        """)
    )
    return {
        "trips": [
            {
                "trip_uuid": r.trip_uuid,
                "title": r.title,
                "start_date": str(r.start_date) if r.start_date else None,
                "end_date": str(r.end_date) if r.end_date else None,
            }
            for r in rows
        ]
    }


async def get_phases(session: AsyncSession, trip_uuid: str) -> dict:
    """Return pre-trip phases of a trip with their checklist items and links."""
    phase_rows = await session.execute(
        text("""
            SELECT id, title, subtitle, icon, short_description,
                   detailed_description, sort_order, is_visible
            FROM trip_phases
            WHERE wetravel_trip_uuid = :trip_uuid AND phase_type = 'pre-trip'
            ORDER BY sort_order ASC
        """),
        {"trip_uuid": trip_uuid},
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
            WHERE p.wetravel_trip_uuid = :trip_uuid AND p.phase_type = 'pre-trip'
            ORDER BY i.sort_order ASC
        """),
        {"trip_uuid": trip_uuid},
    )
    link_rows = await session.execute(
        text("""
            SELECT l.id, l.trip_phase_id, l.label, l.url, l.sort_order
            FROM trip_phase_links l
            JOIN trip_phases p ON p.id = l.trip_phase_id
            WHERE p.wetravel_trip_uuid = :trip_uuid AND p.phase_type = 'pre-trip'
            ORDER BY l.sort_order ASC
        """),
        {"trip_uuid": trip_uuid},
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


async def create_phase(session: AsyncSession, trip_uuid: str, data: dict) -> dict:
    """Create a pre-trip phase in draft state, appended at the end."""
    next_order = await session.scalar(
        text("""
            SELECT COALESCE(MAX(sort_order) + 1, 0) FROM trip_phases
            WHERE wetravel_trip_uuid = :trip_uuid AND phase_type = 'pre-trip'
        """),
        {"trip_uuid": trip_uuid},
    )
    phase_id = await session.scalar(
        text("""
            INSERT INTO trip_phases
                (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                 short_description, detailed_description, sort_order,
                 is_locked_by_default, is_visible, created_at, updated_at)
            VALUES (gen_random_uuid(), :trip_uuid, 'pre-trip', :title, :subtitle, :icon,
                    :short_description, :detailed_description, :sort_order,
                    false, false, now(), now())
            RETURNING id
        """),
        {"trip_uuid": trip_uuid, "sort_order": next_order, **data},
    )
    await session.commit()
    return {"id": str(phase_id), "is_visible": False}


_PHASE_UPDATABLE = ("title", "subtitle", "icon", "short_description", "detailed_description")


async def update_phase(session: AsyncSession, phase_id: str, data: dict) -> dict:
    """Update only the fields explicitly provided."""
    fields = {k: v for k, v in data.items() if k in _PHASE_UPDATABLE and v is not None}
    if not fields:
        return {"id": phase_id, "updated": False}

    assignments = ", ".join(f"{k} = :{k}" for k in fields)
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

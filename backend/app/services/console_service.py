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

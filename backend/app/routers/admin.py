"""Admin HTTP routes — no JWT required, protected by network/sheet access only."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.admin_service import (
    admin_import_trip,
    admin_reset_content,
    admin_reset_progress,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class TripUUIDRequest(BaseModel):
    trip_uuid: str


@router.post("/trips/import")
async def import_trip(body: TripUUIDRequest):
    """Import trip content from Google Sheets into Supabase."""
    try:
        return await admin_import_trip(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/reset-content")
async def reset_content(body: TripUUIDRequest):
    """Delete all phases, checklist, links and activities for a trip."""
    try:
        return await admin_reset_content(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/reset-progress")
async def reset_progress(body: TripUUIDRequest):
    """Delete all traveler checklist and phase progress for a trip."""
    try:
        return await admin_reset_progress(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

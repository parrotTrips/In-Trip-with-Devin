"""Admin HTTP routes — no JWT required, protected by network/sheet access only."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.admin_service import (
    admin_import_trip,
    admin_list_trips,
    admin_reset_content,
    admin_reset_trip,
    admin_start_trip,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class TripUUIDRequest(BaseModel):
    trip_uuid: str


@router.get("/trips")
async def list_trips():
    """Return all active trips (end_date >= today) from wetravel_trips."""
    try:
        return await admin_list_trips()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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


@router.post("/trips/start-trip")
async def start_trip(body: TripUUIDRequest):
    """Start the trip: clear phase progress, preserve checklist, switch to in-trip."""
    try:
        return await admin_start_trip(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/reset-trip")
async def reset_trip(body: TripUUIDRequest):
    """Full reset to pre-trip: clears ALL progress (checklist + phase). For testing."""
    try:
        return await admin_reset_trip(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

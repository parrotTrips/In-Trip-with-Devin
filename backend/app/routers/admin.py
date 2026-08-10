"""Admin HTTP routes — no JWT required, protected by network/sheet access only."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.admin_service import (
    admin_import_activity_participants,
    admin_import_cancellation_policy,
    admin_import_contacts,
    admin_import_emergency_contacts,
    admin_import_faq,
    admin_import_recommendations,
    admin_import_staff,
    admin_import_staff_tasks,
    admin_import_trip,
    admin_list_trips,
    admin_reset_content,
    admin_reset_trip,
    admin_set_user_role,
    admin_start_trip,
    admin_sync_roteiro_to_sheet,
    admin_sync_staff_to_sheet,
    admin_write_staff_bios,
    admin_setup_staff_sheet_headers,
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


@router.post("/trips/sync-to-sheet")
async def sync_roteiro_to_sheet(body: TripUUIDRequest):
    """Write address and max_checkins from DB back to the Roteiro sheet tab."""
    try:
        return await admin_sync_roteiro_to_sheet(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/sync-staff-to-sheet")
async def sync_staff_to_sheet(body: TripUUIDRequest):
    """Write staff tasks and activity participants from DB to the Staff Google Sheet."""
    try:
        return await admin_sync_staff_to_sheet(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/staff-sheet/setup-headers")
async def setup_staff_sheet_headers():
    """Add photo_url and bio columns to Staff sheet header if missing."""
    try:
        return await admin_setup_staff_sheet_headers()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class StaffBiosRequest(BaseModel):
    bios: dict


@router.post("/trips/write-staff-bios")
async def write_staff_bios(body: StaffBiosRequest):
    """Write bio values into the Staff sheet tab. Body: {bios: {phone: bio}}"""
    try:
        return await admin_write_staff_bios("", body.bios)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/reset-content")
async def reset_content(body: TripUUIDRequest):
    """Delete all phases, checklist, links and activities for a trip."""
    try:
        return await admin_reset_content(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/import-faq")
async def import_faq(body: TripUUIDRequest):
    try:
        return await admin_import_faq(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/import-cancellation-policy")
async def import_cancellation_policy(body: TripUUIDRequest):
    try:
        return await admin_import_cancellation_policy(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/import-emergency-contacts")
async def import_emergency_contacts(body: TripUUIDRequest):
    """Import emergency contacts from the Trip Content Google Sheet."""
    try:
        return await admin_import_emergency_contacts(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/import-recommendations")
async def import_recommendations(body: TripUUIDRequest):
    """Import local recommendations from the Trip Content Google Sheet."""
    try:
        return await admin_import_recommendations(body.trip_uuid)
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


@router.post("/trips/import-contacts")
async def import_contacts(body: TripUUIDRequest):
    """Import contacts from the Staff Google Sheet into trip_contacts."""
    try:
        return await admin_import_contacts(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/import-staff")
async def import_staff(body: TripUUIDRequest):
    """Import staff members from the Staff Google Sheet — creates users and links to trip."""
    try:
        return await admin_import_staff(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/import-staff-tasks")
async def import_staff_tasks(body: TripUUIDRequest):
    """Import staff activity tasks from the Staff Google Sheet into staff_tasks."""
    try:
        return await admin_import_staff_tasks(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/import-activity-participants")
async def import_activity_participants(body: TripUUIDRequest):
    """Import controlled activity participant allowlists from the Staff Google Sheet."""
    try:
        return await admin_import_activity_participants(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class SetUserRoleRequest(BaseModel):
    phone: str
    role: str


@router.post("/users/set-role")
async def set_user_role(body: SetUserRoleRequest):
    """Set a user's role (traveler or staff) by phone number."""
    try:
        return await admin_set_user_role(body.phone, body.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

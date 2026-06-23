"""Staff HTTP routes — requires JWT with role=staff."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models.staff import ActivityCheckin, StaffTask, TripContact
from app.db.models.trip import TripActivity, TripPhase, TripTraveler
from app.db.models.user import User
from app.services.qr_service import decode_traveler_qr_payload

router = APIRouter(prefix="/me/staff", tags=["staff"])


class StaffCheckinScanRequest(BaseModel):
    qr_payload: str


async def _get_staff_trip_uuid(user_id: str, session: AsyncSession) -> str:
    """Return the active trip uuid for a staff member."""
    role = await session.scalar(
        text("SELECT role FROM users WHERE id = CAST(:user_id AS uuid)"),
        {"user_id": user_id},
    )
    if role != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")

    result = await session.execute(
        text("""
            SELECT tt.wetravel_trip_uuid
            FROM trip_travelers tt
            JOIN wetravel_trips wt ON wt.trip_uuid = tt.wetravel_trip_uuid
            WHERE tt.user_id = CAST(:user_id AS uuid)
              AND (wt.end_date IS NULL OR wt.end_date::date >= CURRENT_DATE)
            ORDER BY wt.start_date ASC
            LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="No active trip found for this staff member")
    return row["wetravel_trip_uuid"]


@router.get("/trip")
async def get_staff_trip(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return staff itinerary: in-trip days with activities for the active trip."""
    user_id = request.state.user_id
    trip_uuid = await _get_staff_trip_uuid(user_id, session)

    # Fetch trip info
    trip_row = (await session.execute(
        text("SELECT title, start_date, end_date FROM wetravel_trips WHERE trip_uuid = :uuid"),
        {"uuid": trip_uuid},
    )).mappings().first()

    # Fetch in-trip phases (days) ordered by sort_order
    phases_result = await session.execute(
        select(TripPhase)
        .where(
            TripPhase.wetravel_trip_uuid == trip_uuid,
            TripPhase.phase_type == "in-trip",
            TripPhase.is_visible.is_(True),
        )
        .order_by(TripPhase.sort_order)
    )
    phases = phases_result.scalars().all()

    if not phases:
        return {
            "wetravel_trip_uuid": trip_uuid,
            "title": trip_row["title"] if trip_row else "",
            "start_date": str(trip_row["start_date"]) if trip_row else None,
            "end_date": str(trip_row["end_date"]) if trip_row else None,
            "days": [],
        }

    phase_ids = [p.id for p in phases]

    # Fetch all activities for those phases in one query
    activities_result = await session.execute(
        select(TripActivity)
        .where(TripActivity.trip_phase_id.in_(phase_ids))
        .order_by(TripActivity.trip_phase_id, TripActivity.sort_order)
    )
    activities = activities_result.scalars().all()

    activity_ids = [act.id for act in activities]
    tasks_by_activity: dict = {}
    checkin_counts_by_activity: dict = {}
    if activity_ids:
        tasks_result = await session.execute(
            select(StaffTask)
            .where(
                StaffTask.trip_activity_id.in_(activity_ids),
                StaffTask.assigned_to_user_id == user_id,
            )
            .order_by(StaffTask.trip_activity_id, StaffTask.sort_order)
        )
        for task in tasks_result.scalars():
            tasks_by_activity.setdefault(task.trip_activity_id, []).append({
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "sort_order": task.sort_order,
            })

        checkins_result = await session.execute(
            select(
                ActivityCheckin.trip_activity_id,
                func.count(func.distinct(ActivityCheckin.trip_traveler_id)),
            )
            .where(ActivityCheckin.trip_activity_id.in_(activity_ids))
            .group_by(ActivityCheckin.trip_activity_id)
        )
        checkin_counts_by_activity = {
            activity_id: count
            for activity_id, count in checkins_result.all()
        }

    traveler_count = await session.scalar(
        text("""
            SELECT COUNT(*)
            FROM trip_travelers tt
            JOIN users u ON u.id = tt.user_id
            WHERE tt.wetravel_trip_uuid = :uuid
              AND u.role = 'traveler'
        """),
        {"uuid": trip_uuid},
    )

    activities_by_phase: dict = {}
    for act in activities:
        activities_by_phase.setdefault(act.trip_phase_id, []).append({
            "id": str(act.id),
            "name": act.name,
            "activity_type": act.activity_type,
            "starts_at": act.starts_at.isoformat() if act.starts_at else None,
            "duration_minutes": act.duration_minutes,
            "short_description": act.short_description,
            "practical_info": act.practical_info,
            "amount_brl": float(act.amount_brl) if act.amount_brl else None,
            "sort_order": act.sort_order,
            "checkin_count": checkin_counts_by_activity.get(act.id, 0),
            "traveler_count": traveler_count or 0,
            "staff_tasks": tasks_by_activity.get(act.id, []),
        })

    return {
        "wetravel_trip_uuid": trip_uuid,
        "title": trip_row["title"] if trip_row else "",
        "start_date": str(trip_row["start_date"]) if trip_row else None,
        "end_date": str(trip_row["end_date"]) if trip_row else None,
        "days": [
            {
                "id": str(p.id),
                "title": p.title,
                "subtitle": p.subtitle,
                "icon": p.icon,
                "sort_order": p.sort_order,
                "starts_at": p.starts_at.isoformat() if p.starts_at else None,
                "activities": activities_by_phase.get(p.id, []),
            }
            for p in phases
        ],
    }


@router.get("/trip/contacts")
async def get_staff_contacts(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return contacts for the active trip, grouped by category."""
    user_id = request.state.user_id
    trip_uuid = await _get_staff_trip_uuid(user_id, session)

    contacts_result = await session.execute(
        select(TripContact)
        .where(TripContact.wetravel_trip_uuid == trip_uuid)
        .order_by(TripContact.category, TripContact.sort_order)
    )
    contacts = contacts_result.scalars().all()

    grouped: dict[str, list] = {}
    for c in contacts:
        grouped.setdefault(c.category, []).append({
            "id": str(c.id),
            "name": c.name,
            "role": c.role,
            "phone": c.phone,
            "sort_order": c.sort_order,
        })

    return {
        "wetravel_trip_uuid": trip_uuid,
        "contacts": [
            {"category": cat, "contacts": items}
            for cat, items in grouped.items()
        ],
    }


@router.post("/activities/{activity_id}/checkins/scan")
async def scan_activity_checkin(
    activity_id: uuid.UUID,
    body: StaffCheckinScanRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Scan a traveler's QR code into a staff activity."""
    try:
        payload = decode_traveler_qr_payload(body.qr_payload)
        trip_traveler_id = uuid.UUID(str(payload["trip_traveler_id"]))
        payload_trip_uuid = payload["trip_uuid"]
    except (KeyError, TypeError, ValueError, JWTError):
        raise HTTPException(status_code=400, detail="Invalid QR payload") from None

    staff_user_id = uuid.UUID(str(request.state.user_id))
    staff_trip_uuid = await _get_staff_trip_uuid(str(staff_user_id), session)

    activity_trip_uuid = await session.scalar(
        select(TripPhase.wetravel_trip_uuid)
        .join(TripActivity, TripActivity.trip_phase_id == TripPhase.id)
        .where(TripActivity.id == activity_id)
    )
    if activity_trip_uuid is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity_trip_uuid != staff_trip_uuid:
        raise HTTPException(status_code=403, detail="Activity is outside staff active trip")

    trip_traveler = await session.scalar(
        select(TripTraveler).where(TripTraveler.id == trip_traveler_id)
    )
    if trip_traveler is None:
        raise HTTPException(status_code=404, detail="Traveler not found")
    if payload_trip_uuid != staff_trip_uuid or trip_traveler.wetravel_trip_uuid != staff_trip_uuid:
        raise HTTPException(status_code=403, detail="Traveler is outside staff active trip")

    result = await session.execute(
        insert(ActivityCheckin)
        .values(
            trip_activity_id=activity_id,
            trip_traveler_id=trip_traveler_id,
            scanned_by_user_id=staff_user_id,
        )
        .on_conflict_do_nothing(
            index_elements=["trip_activity_id", "trip_traveler_id"],
        )
        .returning(
            ActivityCheckin.id,
            ActivityCheckin.trip_activity_id,
            ActivityCheckin.trip_traveler_id,
            ActivityCheckin.checked_in_at,
            ActivityCheckin.scanned_by_user_id,
        )
    )
    inserted = result.mappings().first()
    if inserted:
        await session.commit()
        return {
            "status": "checked_in",
            "checkin_id": str(inserted["id"]),
            "trip_activity_id": str(inserted["trip_activity_id"]),
            "trip_traveler_id": str(inserted["trip_traveler_id"]),
            "checked_in_at": inserted["checked_in_at"].isoformat(),
            "scanned_by_user_id": str(inserted["scanned_by_user_id"]),
        }

    existing = (
        await session.execute(
            select(ActivityCheckin, User.full_name)
            .join(User, User.id == ActivityCheckin.scanned_by_user_id)
            .where(
                ActivityCheckin.trip_activity_id == activity_id,
                ActivityCheckin.trip_traveler_id == trip_traveler_id,
            )
        )
    ).first()
    if existing is None:
        raise HTTPException(status_code=500, detail="Check-in conflict could not be resolved")

    checkin, scanned_by_name = existing
    return {
        "status": "already_checked_in",
        "checkin_id": str(checkin.id),
        "trip_activity_id": str(checkin.trip_activity_id),
        "trip_traveler_id": str(checkin.trip_traveler_id),
        "checked_in_at": checkin.checked_in_at.isoformat(),
        "scanned_by_user_id": str(checkin.scanned_by_user_id),
        "scanned_by_name": scanned_by_name,
    }

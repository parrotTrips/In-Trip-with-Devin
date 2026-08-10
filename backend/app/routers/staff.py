"""Staff HTTP routes — requires JWT with role=staff."""

import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models.staff import (
    ActivityCheckin,
    ActivityCheckinScanEvent,
    ActivityParticipant,
    StaffTask,
    TripAnnouncement,
    TripContact,
)
from app.db.models.trip import TripActivity, TripPhase, TripTraveler
from app.db.models.user import User
from app.services.qr_service import decode_traveler_qr_payload

router = APIRouter(prefix="/me/staff", tags=["staff"])


class StaffCheckinScanRequest(BaseModel):
    qr_payload: str


class AnnouncementRequest(BaseModel):
    title: str
    body: str
    is_anonymous: bool = False


def _payload_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _record_scan_event(
    session: AsyncSession,
    *,
    trip_activity_id: uuid.UUID | None,
    trip_traveler_id: uuid.UUID | None,
    scanned_by_user_id: uuid.UUID,
    status: str,
    raw_payload: str,
    failure_reason: str | None = None,
) -> None:
    session.add(
        ActivityCheckinScanEvent(
            trip_activity_id=trip_activity_id,
            trip_traveler_id=trip_traveler_id,
            scanned_by_user_id=scanned_by_user_id,
            status=status,
            failure_reason=failure_reason,
            raw_payload_hash=_payload_hash(raw_payload),
        )
    )


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

        # Per-step checkin details: name, traveler_id, checked_in_at
        checkins_result = await session.execute(
            text("""
                SELECT ac.trip_activity_id, ac.scan_number, ac.trip_traveler_id,
                       u.full_name as traveler_name,
                       ac.checked_in_at
                FROM activity_checkins ac
                JOIN trip_travelers tt ON tt.id = ac.trip_traveler_id
                JOIN users u ON u.id = tt.user_id
                WHERE ac.trip_activity_id = ANY(:ids)
                ORDER BY ac.trip_activity_id, ac.scan_number, ac.checked_in_at
            """),
            {"ids": activity_ids},
        )
        # Build: {activity_id: {step: [{name, checked_in_at}]}} and set of checked-in traveler_ids per activity
        checkin_steps_by_activity: dict = {}
        checked_in_traveler_ids_by_activity: dict = {}
        for row in checkins_result.mappings():
            act_id = row["trip_activity_id"]
            step = row["scan_number"]
            name = row["traveler_name"] or "Unknown"
            checked_in_at = row["checked_in_at"].isoformat() if row["checked_in_at"] else None
            traveler_id = str(row["trip_traveler_id"])
            checkin_steps_by_activity.setdefault(act_id, {}).setdefault(step, []).append(
                {"name": name, "checked_in_at": checked_in_at}
            )
            checked_in_traveler_ids_by_activity.setdefault(act_id, set()).add(traveler_id)

    total_traveler_count = await session.scalar(
        text("""
            SELECT COUNT(*)
            FROM trip_travelers tt
            JOIN users u ON u.id = tt.user_id
            WHERE tt.wetravel_trip_uuid = :uuid
              AND u.role = 'traveler'
        """),
        {"uuid": trip_uuid},
    )

    # Per-activity allowed participant counts (only for controlled activities)
    activity_ids = [act.id for act in activities]
    controlled_counts_result = await session.execute(
        text("""
            SELECT trip_activity_id, COUNT(*) as cnt
            FROM activity_participants
            WHERE trip_activity_id = ANY(:ids)
              AND status = 'allowed'
            GROUP BY trip_activity_id
        """),
        {"ids": activity_ids},
    )
    controlled_counts = {row.trip_activity_id: row.cnt for row in controlled_counts_result}

    # All traveler names for the trip (for absent list)
    all_travelers_result = await session.execute(
        text("""
            SELECT tt.id as traveler_id, u.full_name
            FROM trip_travelers tt
            JOIN users u ON u.id = tt.user_id
            WHERE tt.wetravel_trip_uuid = :uuid AND u.role = 'traveler'
            ORDER BY u.full_name
        """),
        {"uuid": trip_uuid},
    )
    all_travelers = [
        {"id": str(r.traveler_id), "name": r.full_name or "Unknown"}
        for r in all_travelers_result.mappings()
    ]

    # Per-activity allowed participants (for controlled activities)
    allowed_travelers_result = await session.execute(
        text("""
            SELECT ap.trip_activity_id, tt.id as traveler_id, u.full_name
            FROM activity_participants ap
            JOIN trip_travelers tt ON tt.id = ap.trip_traveler_id
            JOIN users u ON u.id = tt.user_id
            WHERE ap.trip_activity_id = ANY(:ids) AND ap.status = 'allowed'
            ORDER BY u.full_name
        """),
        {"ids": activity_ids},
    )
    allowed_by_activity: dict = {}
    for row in allowed_travelers_result.mappings():
        allowed_by_activity.setdefault(str(row.trip_activity_id), []).append(
            {"id": str(row.traveler_id), "name": row.full_name or "Unknown"}
        )

    activities_by_phase: dict = {}
    for act in activities:
        act_id_str = str(act.id)
        is_controlled = act_id_str in allowed_by_activity
        expected_travelers = allowed_by_activity[act_id_str] if is_controlled else all_travelers
        traveler_count = controlled_counts.get(act.id, total_traveler_count or 0)

        steps_data = checkin_steps_by_activity.get(act.id, {})
        checked_in_ids = checked_in_traveler_ids_by_activity.get(act.id, set())
        checkin_steps = [
            {"step": step, "count": len(entries), "travelers": [e["name"] for e in entries], "details": entries}
            for step, entries in sorted(steps_data.items())
        ]
        absent_travelers = [t["name"] for t in expected_travelers if t["id"] not in checked_in_ids]
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
            "address": act.address,
            "max_checkins": act.max_checkins,
            "checkin_steps": checkin_steps,
            "absent_travelers": absent_travelers,
            "traveler_count": traveler_count,
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


@router.post("/announcements")
async def create_announcement(
    body: AnnouncementRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Send a trip announcement to all travelers. Staff only."""
    staff_user_id = uuid.UUID(str(request.state.user_id))
    trip_uuid = await _get_staff_trip_uuid(str(staff_user_id), session)

    ann = TripAnnouncement(
        id=uuid.uuid4(),
        wetravel_trip_uuid=trip_uuid,
        title=body.title.strip(),
        body=body.body.strip(),
        sent_by_user_id=staff_user_id,
        is_anonymous=body.is_anonymous,
    )
    session.add(ann)
    await session.commit()

    return {
        "id": str(ann.id),
        "title": ann.title,
        "body": ann.body,
        "created_at": ann.created_at.isoformat(),
    }


@router.get("/announcements")
async def list_announcements(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """List all announcements for the staff's active trip, newest first."""
    staff_user_id = str(request.state.user_id)
    trip_uuid = await _get_staff_trip_uuid(staff_user_id, session)

    rows = (await session.execute(
        select(TripAnnouncement, User.full_name)
        .join(User, User.id == TripAnnouncement.sent_by_user_id)
        .where(TripAnnouncement.wetravel_trip_uuid == trip_uuid)
        .order_by(TripAnnouncement.created_at.desc())
    )).all()

    return {
        "announcements": [
            {
                "id": str(ann.id),
                "title": ann.title,
                "body": ann.body,
                "sent_by": name,
                "sent_by_user_id": str(ann.sent_by_user_id),
                "is_anonymous": ann.is_anonymous,
                "created_at": ann.created_at.isoformat(),
            }
            for ann, name in rows
        ]
    }


class AnnouncementUpdateRequest(BaseModel):
    title: str
    body: str


@router.put("/announcements/{announcement_id}")
async def update_announcement(
    announcement_id: uuid.UUID,
    body: AnnouncementUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Edit an announcement. Only the original sender can edit."""
    staff_user_id = uuid.UUID(str(request.state.user_id))

    ann = await session.scalar(
        select(TripAnnouncement).where(TripAnnouncement.id == announcement_id)
    )
    if ann is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    if ann.sent_by_user_id != staff_user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own announcements")

    ann.title = body.title.strip()
    ann.body = body.body.strip()
    await session.commit()

    return {"id": str(ann.id), "title": ann.title, "body": ann.body}


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Delete an announcement. Only the original sender can delete."""
    staff_user_id = uuid.UUID(str(request.state.user_id))

    ann = await session.scalar(
        select(TripAnnouncement).where(TripAnnouncement.id == announcement_id)
    )
    if ann is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    if ann.sent_by_user_id != staff_user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own announcements")

    await session.delete(ann)
    await session.commit()

    return {"status": "deleted"}


@router.get("/activities/{activity_id}/travelers")
async def get_activity_travelers(
    activity_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return travelers eligible for check-in in this activity, with pre-generated QR payloads."""
    from app.services.qr_service import create_traveler_qr_payload

    staff_user_id = str(request.state.user_id)
    staff_trip_uuid = await _get_staff_trip_uuid(staff_user_id, session)

    # Check if controlled activity
    participant_count = await session.scalar(
        select(func.count())
        .select_from(ActivityParticipant)
        .where(ActivityParticipant.trip_activity_id == activity_id)
    )

    if participant_count:
        # Controlled — return only allowed participants
        rows = await session.execute(
            text("""
                SELECT tt.id as traveler_id, u.full_name
                FROM activity_participants ap
                JOIN trip_travelers tt ON tt.id = ap.trip_traveler_id
                JOIN users u ON u.id = tt.user_id
                WHERE ap.trip_activity_id = :act_id AND ap.status = 'allowed'
                ORDER BY u.full_name
            """),
            {"act_id": str(activity_id)},
        )
    else:
        # Open — return all travelers in the trip
        rows = await session.execute(
            text("""
                SELECT tt.id as traveler_id, u.full_name
                FROM trip_travelers tt
                JOIN users u ON u.id = tt.user_id
                WHERE tt.wetravel_trip_uuid = :trip_uuid AND u.role = 'traveler'
                ORDER BY u.full_name
            """),
            {"trip_uuid": staff_trip_uuid},
        )

    travelers = []
    for row in rows.mappings():
        qr_payload = create_traveler_qr_payload(
            str(row["traveler_id"]), staff_trip_uuid
        )
        travelers.append({
            "id": str(row["traveler_id"]),
            "name": row["full_name"] or "Unknown",
            "qr_payload": qr_payload,
        })

    return {"travelers": travelers}


@router.post("/activities/{activity_id}/checkins/scan")
async def scan_activity_checkin(
    activity_id: uuid.UUID,
    body: StaffCheckinScanRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Scan a traveler's QR code into a staff activity."""
    staff_user_id = uuid.UUID(str(request.state.user_id))
    staff_trip_uuid = await _get_staff_trip_uuid(str(staff_user_id), session)

    try:
        payload = decode_traveler_qr_payload(body.qr_payload)
        trip_traveler_id = uuid.UUID(str(payload["trip_traveler_id"]))
        payload_trip_uuid = payload["trip_uuid"]
    except (KeyError, TypeError, ValueError, JWTError):
        await _record_scan_event(
            session,
            trip_activity_id=None,
            trip_traveler_id=None,
            scanned_by_user_id=staff_user_id,
            status="invalid_qr",
            raw_payload=body.qr_payload,
            failure_reason="Invalid QR payload",
        )
        await session.commit()
        raise HTTPException(status_code=400, detail="Invalid QR payload") from None

    activity_trip_uuid = await session.scalar(
        select(TripPhase.wetravel_trip_uuid)
        .join(TripActivity, TripActivity.trip_phase_id == TripPhase.id)
        .where(TripActivity.id == activity_id)
    )
    if activity_trip_uuid is None:
        await _record_scan_event(
            session,
            trip_activity_id=None,
            trip_traveler_id=trip_traveler_id,
            scanned_by_user_id=staff_user_id,
            status="activity_not_found",
            raw_payload=body.qr_payload,
            failure_reason="Activity not found",
        )
        await session.commit()
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity_trip_uuid != staff_trip_uuid:
        await _record_scan_event(
            session,
            trip_activity_id=activity_id,
            trip_traveler_id=trip_traveler_id,
            scanned_by_user_id=staff_user_id,
            status="activity_outside_staff_trip",
            raw_payload=body.qr_payload,
            failure_reason="Activity is outside staff active trip",
        )
        await session.commit()
        raise HTTPException(status_code=403, detail="Activity is outside staff active trip")

    trip_traveler = await session.scalar(
        select(TripTraveler).where(TripTraveler.id == trip_traveler_id)
    )
    if trip_traveler is None:
        await _record_scan_event(
            session,
            trip_activity_id=activity_id,
            trip_traveler_id=None,
            scanned_by_user_id=staff_user_id,
            status="traveler_not_found",
            raw_payload=body.qr_payload,
            failure_reason="Traveler not found",
        )
        await session.commit()
        raise HTTPException(status_code=404, detail="Traveler not found")
    if payload_trip_uuid != staff_trip_uuid or trip_traveler.wetravel_trip_uuid != staff_trip_uuid:
        await _record_scan_event(
            session,
            trip_activity_id=activity_id,
            trip_traveler_id=trip_traveler_id,
            scanned_by_user_id=staff_user_id,
            status="traveler_outside_staff_trip",
            raw_payload=body.qr_payload,
            failure_reason="Traveler is outside staff active trip",
        )
        await session.commit()
        raise HTTPException(status_code=403, detail="Traveler is outside staff active trip")
    traveler_role = await session.scalar(
        select(User.role).where(User.id == trip_traveler.user_id)
    )
    if traveler_role != "traveler":
        await _record_scan_event(
            session,
            trip_activity_id=activity_id,
            trip_traveler_id=trip_traveler_id,
            scanned_by_user_id=staff_user_id,
            status="not_traveler",
            raw_payload=body.qr_payload,
            failure_reason="QR code does not belong to a traveler",
        )
        await session.commit()
        raise HTTPException(status_code=403, detail="QR code does not belong to a traveler")

    participant_count = await session.scalar(
        select(func.count())
        .select_from(ActivityParticipant)
        .where(ActivityParticipant.trip_activity_id == activity_id)
    )
    if participant_count:
        allowed = await session.scalar(
            select(ActivityParticipant.id).where(
                ActivityParticipant.trip_activity_id == activity_id,
                ActivityParticipant.trip_traveler_id == trip_traveler_id,
                ActivityParticipant.status == "allowed",
            )
        )
        if allowed is None:
            await _record_scan_event(
                session,
                trip_activity_id=activity_id,
                trip_traveler_id=trip_traveler_id,
                scanned_by_user_id=staff_user_id,
                status="not_authorized_for_activity",
                raw_payload=body.qr_payload,
                failure_reason="Traveler is not authorized for this activity",
            )
            await session.commit()
            raise HTTPException(status_code=403, detail="Traveler is not authorized for this activity")

    # Fetch activity to get max_checkins
    activity = await session.scalar(select(TripActivity).where(TripActivity.id == activity_id))
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    max_checkins = activity.max_checkins or 1

    # Count how many scans this traveler already has for this activity
    existing_scans = await session.execute(
        select(ActivityCheckin)
        .where(
            ActivityCheckin.trip_activity_id == activity_id,
            ActivityCheckin.trip_traveler_id == trip_traveler_id,
        )
        .order_by(ActivityCheckin.scan_number)
    )
    existing_checkins = existing_scans.scalars().all()
    next_scan_number = len(existing_checkins) + 1

    if next_scan_number > max_checkins:
        await _record_scan_event(
            session,
            trip_activity_id=activity_id,
            trip_traveler_id=trip_traveler_id,
            scanned_by_user_id=staff_user_id,
            status="already_checked_in",
            raw_payload=body.qr_payload,
        )
        await session.commit()
        traveler_name_row = await session.execute(
            select(User.full_name)
            .join(TripTraveler, TripTraveler.user_id == User.id)
            .where(TripTraveler.id == trip_traveler_id)
        )
        traveler_name = traveler_name_row.scalar()
        last = existing_checkins[-1]
        scanned_by_row = await session.scalar(select(User.full_name).where(User.id == last.scanned_by_user_id))
        return {
            "status": "already_checked_in",
            "checkin_id": str(last.id),
            "trip_activity_id": str(last.trip_activity_id),
            "trip_traveler_id": str(last.trip_traveler_id),
            "checked_in_at": last.checked_in_at.isoformat(),
            "scanned_by_user_id": str(last.scanned_by_user_id),
            "scanned_by_name": scanned_by_row,
            "scan_number": last.scan_number,
            "max_checkins": max_checkins,
            "traveler_name": traveler_name,
        }

    new_checkin = ActivityCheckin(
        trip_activity_id=activity_id,
        trip_traveler_id=trip_traveler_id,
        scanned_by_user_id=staff_user_id,
        scan_number=next_scan_number,
    )
    session.add(new_checkin)
    await session.flush()
    await _record_scan_event(
        session,
        trip_activity_id=activity_id,
        trip_traveler_id=trip_traveler_id,
        scanned_by_user_id=staff_user_id,
        status="checked_in",
        raw_payload=body.qr_payload,
    )
    await session.commit()

    traveler_name_row = await session.execute(
        select(User.full_name)
        .join(TripTraveler, TripTraveler.user_id == User.id)
        .where(TripTraveler.id == trip_traveler_id)
    )
    traveler_name = traveler_name_row.scalar()
    return {
        "status": "checked_in",
        "checkin_id": str(new_checkin.id),
        "trip_activity_id": str(new_checkin.trip_activity_id),
        "trip_traveler_id": str(new_checkin.trip_traveler_id),
        "checked_in_at": new_checkin.checked_in_at.isoformat(),
        "scanned_by_user_id": str(new_checkin.scanned_by_user_id),
        "scan_number": next_scan_number,
        "max_checkins": max_checkins,
        "traveler_name": traveler_name,
    }


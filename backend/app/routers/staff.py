"""Staff HTTP routes — requires JWT with role=staff."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models.staff import StaffTask, TripContact
from app.db.models.trip import TripActivity, TripPhase

router = APIRouter(prefix="/me/staff", tags=["staff"])


async def _get_staff_trip_uuid(user_id: str, session: AsyncSession) -> str:
    """Return the active trip uuid for a staff member."""
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

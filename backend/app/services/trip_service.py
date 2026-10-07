"""Trip service: fases, atividades e viajantes."""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, date as _date, datetime as _datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.trip import (
    TripActivity,
    TripPhase,
    TripPhaseChecklistItem,
    TripPhaseLink,
    TripTraveler,
)
from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.staff import TripStaff
from app.db.models.traveler import TravelerProfile
from app.db.models.user import User
from app.services.trip_membership_service import require_trip_membership

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def resolve_trip_mode(
    stored_mode: str,
    start_date: _date | str | None,
    now: _datetime,
    timezone: ZoneInfo = SAO_PAULO_TZ,
) -> str:
    """The trip becomes in-trip on its start date (São Paulo time).

    A manual "Start Trip" can still switch it earlier; the stored mode wins then.
    """
    if stored_mode != "pre-trip" or start_date is None:
        return stored_mode
    start_date = _as_date(start_date)
    if start_date is None:
        return stored_mode
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return "in-trip" if now.astimezone(timezone).date() >= start_date else stored_mode


async def _get_trip_settings(trip_uuid: str, session: AsyncSession) -> dict:
    """Return the effective mode and ideal_pace_phase_id for a trip. Defaults to pre-trip/None."""
    from sqlalchemy import text as _text
    result = await session.execute(
        _text(
            "SELECT s.mode, s.ideal_pace_phase_id, w.start_date, w.end_date"
            " FROM wetravel_trips w"
            " LEFT JOIN trip_settings s ON s.trip_uuid = w.trip_uuid"
            " WHERE w.trip_uuid = :uuid"
        ),
        {"uuid": trip_uuid},
    )
    row = result.mappings().first()
    stored_mode = (row["mode"] if row else None) or "pre-trip"
    start_date = row["start_date"] if row else None
    return {
        "mode": resolve_trip_mode(stored_mode, start_date, _datetime.now(UTC)),
        "ideal_pace_phase_id": row["ideal_pace_phase_id"] if row else None,
        "end_date": _as_date(row["end_date"]) if row else None,
    }


def _as_date(value) -> _date | None:
    if value is None or value == "":
        return None
    if isinstance(value, _date):
        return value
    return _date.fromisoformat(str(value)[:10])


def _phase_order_key(phase) -> tuple[int, int]:
    """Trip Wrap-up (post-trip) phases always come last in the journey."""
    phase_type = phase["phase_type"] if isinstance(phase, dict) else phase.phase_type
    sort_order = phase["sort_order"] if isinstance(phase, dict) else phase.sort_order
    return (1 if phase_type == "post-trip" else 0, sort_order)


async def _get_trip_mode(trip_uuid: str, session: AsyncSession) -> str:
    settings = await _get_trip_settings(trip_uuid, session)
    return settings["mode"]


def compute_in_trip_phase_completions(
    phases: list[dict], now: _datetime
) -> dict[str, bool]:
    """Return {phase_id: bool} for in-trip phases only.
    A phase has started (True) if starts_at is set and starts_at <= now.
    Pre-trip phases are not included."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    result: dict[str, bool] = {}
    for phase in phases:
        if phase["phase_type"] != "in-trip":
            continue
        starts_at = phase["starts_at"]
        if starts_at is None:
            result[phase["id"]] = False
        else:
            if isinstance(starts_at, str):
                starts_at = _datetime.fromisoformat(starts_at)
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=UTC)
            result[phase["id"]] = starts_at <= now
    return result


def compute_checklist_completed_phase_ids(
    items_by_phase: dict[str, list[dict]],
    done_item_ids: set[str],
) -> set[str]:
    """Phases whose checklist is done: every required item, or every item when none is required."""
    completed: set[str] = set()
    for phase_id, items in items_by_phase.items():
        if not items:
            continue
        needed = [i for i in items if i["is_required"]] or items
        if all(i["id"] in done_item_ids for i in needed):
            completed.add(phase_id)
    return completed


async def _completed_phase_ids_by_traveler(
    trip_traveler_ids: list[_uuid.UUID],
    phase_ids: list[_uuid.UUID],
    session: AsyncSession,
) -> dict[_uuid.UUID, set[str]]:
    """Phases each traveler finished, via "Mark as Completed" or a completed checklist."""
    completed: dict[_uuid.UUID, set[str]] = {tt_id: set() for tt_id in trip_traveler_ids}
    if not trip_traveler_ids or not phase_ids:
        return completed

    manual = await session.scalars(
        select(TravelerPhaseProgress).where(
            TravelerPhaseProgress.trip_traveler_id.in_(trip_traveler_ids),
            TravelerPhaseProgress.trip_phase_id.in_(phase_ids),
            TravelerPhaseProgress.is_completed.is_(True),
        )
    )
    for row in manual:
        completed[row.trip_traveler_id].add(str(row.trip_phase_id))

    items_by_phase: dict[str, list[dict]] = {}
    for item in await session.scalars(
        select(TripPhaseChecklistItem).where(TripPhaseChecklistItem.trip_phase_id.in_(phase_ids))
    ):
        items_by_phase.setdefault(str(item.trip_phase_id), []).append(
            {"id": str(item.id), "is_required": item.is_required}
        )
    if not items_by_phase:
        return completed

    done_items: dict[_uuid.UUID, set[str]] = {}
    for row in await session.scalars(
        select(TravelerChecklistProgress).where(
            TravelerChecklistProgress.trip_traveler_id.in_(trip_traveler_ids),
            TravelerChecklistProgress.is_completed.is_(True),
        )
    ):
        done_items.setdefault(row.trip_traveler_id, set()).add(str(row.trip_phase_checklist_item_id))
    for tt_id, item_ids in done_items.items():
        completed[tt_id] |= compute_checklist_completed_phase_ids(items_by_phase, item_ids)
    return completed


def _phase_local_date(phase: dict, timezone: ZoneInfo):
    starts_at = phase["starts_at"]
    if starts_at is None:
        return None
    if isinstance(starts_at, str):
        starts_at = _datetime.fromisoformat(starts_at)
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=UTC)
    return starts_at.astimezone(timezone).date()


def compute_current_phase_id(
    phases: list[dict],
    completed_phase_ids: set[str],
    trip_mode: str,
    now: _datetime,
    timezone: ZoneInfo = SAO_PAULO_TZ,
    trip_end_date: _date | None = None,
) -> str | None:
    if not phases:
        return None

    ordered_phases = sorted(phases, key=_phase_order_key)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    today = now.astimezone(timezone).date()

    # From the last trip day on, the traveler is on the Trip Wrap-up.
    wrap_up_phases = [p for p in ordered_phases if p["phase_type"] == "post-trip"]
    if wrap_up_phases and trip_end_date is not None and today >= trip_end_date:
        for phase in wrap_up_phases:
            if phase["id"] not in completed_phase_ids:
                return phase["id"]
        return wrap_up_phases[-1]["id"]
    journey_phases = [p for p in ordered_phases if p["phase_type"] != "post-trip"] or ordered_phases

    if trip_mode == "in-trip":
        in_trip_phases = [p for p in journey_phases if p["phase_type"] == "in-trip"]
        if in_trip_phases:
            current_phase = in_trip_phases[0]

            for phase in in_trip_phases:
                phase_date = _phase_local_date(phase, timezone)
                if phase_date is not None and phase_date <= today:
                    current_phase = phase

            return current_phase["id"]

    for phase in journey_phases:
        if phase["id"] not in completed_phase_ids:
            return phase["id"]
    return journey_phases[-1]["id"]


async def get_trip_phases(user_id: str, trip_id: str, session: AsyncSession) -> dict:
    trip_traveler = await require_trip_membership(user_id, trip_id, session)
    trip_uuid = trip_id

    phases_result = await session.execute(
        select(TripPhase)
        .where(TripPhase.wetravel_trip_uuid == trip_uuid, TripPhase.is_visible.is_(True))
        .order_by(TripPhase.sort_order)
    )
    phases = sorted(phases_result.scalars().all(), key=_phase_order_key)

    if not phases:
        trip_mode = await _get_trip_mode(trip_uuid, session)
        return {
            "wetravel_trip_uuid": trip_uuid,
            "trip_mode": trip_mode,
            "phases": [],
            "completed_phase_ids": [],
        }

    phase_ids = [p.id for p in phases]

    checklist_result = await session.execute(
        select(TripPhaseChecklistItem)
        .where(TripPhaseChecklistItem.trip_phase_id.in_(phase_ids))
        .order_by(TripPhaseChecklistItem.trip_phase_id, TripPhaseChecklistItem.sort_order)
    )
    checklist_by_phase: dict[_uuid.UUID, list] = {}
    for item in checklist_result.scalars():
        checklist_by_phase.setdefault(item.trip_phase_id, []).append({
            "id": str(item.id),
            "label": item.label,
            "sort_order": item.sort_order,
            "is_required": item.is_required,
        })

    links_result = await session.execute(
        select(TripPhaseLink)
        .where(TripPhaseLink.trip_phase_id.in_(phase_ids))
        .order_by(TripPhaseLink.trip_phase_id, TripPhaseLink.sort_order)
    )
    links_by_phase: dict[_uuid.UUID, list] = {}
    for link in links_result.scalars():
        links_by_phase.setdefault(link.trip_phase_id, []).append({
            "id": str(link.id),
            "label": link.label,
            "url": link.url,
            "sort_order": link.sort_order,
        })

    settings = await _get_trip_settings(trip_uuid, session)
    completed = await _completed_phase_ids_by_traveler([trip_traveler.id], phase_ids, session)
    return {
        "wetravel_trip_uuid": trip_uuid,
        "trip_mode": settings["mode"],
        "ideal_pace_phase_id": settings["ideal_pace_phase_id"],
        "completed_phase_ids": sorted(completed[trip_traveler.id]),
        "phases": [
            {
                "id": str(p.id),
                "phase_type": p.phase_type,
                "title": p.title,
                "subtitle": p.subtitle,
                "icon": p.icon,
                "short_description": p.short_description,
                "detailed_description": p.detailed_description,
                "sort_order": p.sort_order,
                "starts_at": p.starts_at.isoformat() if p.starts_at else None,
                "is_locked_by_default": p.is_locked_by_default,
                "checklist_items": checklist_by_phase.get(p.id, []),
                "links": links_by_phase.get(p.id, []),
            }
            for p in phases
        ],
    }


async def get_trip_phase_detail(
    user_id: str, trip_id: str, phase_id: str, session: AsyncSession
) -> dict:
    await require_trip_membership(user_id, trip_id, session)
    trip_uuid = trip_id

    try:
        pid = _uuid.UUID(phase_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Fase não encontrada")

    phase = await session.scalar(
        select(TripPhase).where(
            TripPhase.id == pid,
            TripPhase.wetravel_trip_uuid == trip_uuid,
        )
    )
    if not phase:
        raise HTTPException(status_code=404, detail="Fase não encontrada")

    checklist_result = await session.execute(
        select(TripPhaseChecklistItem)
        .where(TripPhaseChecklistItem.trip_phase_id == pid)
        .order_by(TripPhaseChecklistItem.sort_order)
    )
    links_result = await session.execute(
        select(TripPhaseLink)
        .where(TripPhaseLink.trip_phase_id == pid)
        .order_by(TripPhaseLink.sort_order)
    )
    activities_result = await session.execute(
        select(TripActivity)
        .where(TripActivity.trip_phase_id == pid)
        .order_by(TripActivity.sort_order)
    )

    return {
        "id": str(phase.id),
        "phase_type": phase.phase_type,
        "title": phase.title,
        "subtitle": phase.subtitle,
        "icon": phase.icon,
        "short_description": phase.short_description,
        "detailed_description": phase.detailed_description,
        "sort_order": phase.sort_order,
        "starts_at": phase.starts_at.isoformat() if phase.starts_at else None,
        "is_locked_by_default": phase.is_locked_by_default,
        "checklist_items": [
            {"id": str(i.id), "label": i.label, "sort_order": i.sort_order, "is_required": i.is_required}
            for i in checklist_result.scalars()
        ],
        "links": [
            {"id": str(l.id), "label": l.label, "url": l.url, "sort_order": l.sort_order}
            for l in links_result.scalars()
        ],
        "activities": [
            {
                "id": str(a.id),
                "name": a.name,
                "activity_type": a.activity_type,
                "starts_at": a.starts_at.isoformat() if a.starts_at else None,
                "duration_minutes": a.duration_minutes,
                "short_description": a.short_description,
                "practical_info": a.practical_info,
                "address": a.address,
                "amount_brl": float(a.amount_brl) if a.amount_brl is not None else None,
                "sort_order": a.sort_order,
            }
            for a in activities_result.scalars()
        ],
    }


async def _traveler_positions(trip_uuid: str, session: AsyncSession) -> dict:
    """Travelers (staff excluded) with their completed phases and current phase."""
    not_staff_on_this_trip = ~(
        select(TripStaff.id)
        .where(
            TripStaff.wetravel_trip_uuid == trip_uuid,
            TripStaff.user_id == TripTraveler.user_id,
        )
        .exists()
    )
    tt_result = await session.execute(
        select(TripTraveler, User, TravelerProfile.preferred_name)
        .join(User, User.id == TripTraveler.user_id)
        .outerjoin(
            TravelerProfile,
            TravelerProfile.trip_traveler_id == TripTraveler.id,
        )
        .where(
            TripTraveler.wetravel_trip_uuid == trip_uuid,
            not_staff_on_this_trip,
        )
    )
    rows = tt_result.all()
    settings = await _get_trip_settings(trip_uuid, session)
    if not rows:
        return {"trip_mode": settings["mode"], "phases": [], "travelers": []}

    tt_ids = [tt.id for tt, _, _ in rows]

    all_phases_result = await session.execute(
        select(TripPhase)
        .where(TripPhase.wetravel_trip_uuid == trip_uuid, TripPhase.is_visible.is_(True))
        .order_by(TripPhase.sort_order)
    )
    all_phases = sorted(all_phases_result.scalars().all(), key=_phase_order_key)

    phase_dicts = [
        {
            "id": str(p.id),
            "phase_type": p.phase_type,
            "title": p.title,
            "subtitle": p.subtitle,
            "starts_at": p.starts_at,
            "sort_order": p.sort_order,
        }
        for p in all_phases
    ]
    now = _datetime.now(UTC)
    date_completions = compute_in_trip_phase_completions(phase_dicts, now)

    db_completed_ids = await _completed_phase_ids_by_traveler(
        tt_ids, [p.id for p in all_phases], session
    )

    travelers = []
    for tt, user, preferred_name in rows:
        completed_phase_ids = db_completed_ids.get(tt.id, set()) | {
            pid for pid, is_completed in date_completions.items() if is_completed
        }
        travelers.append({
            "trip_traveler_id": tt.id,
            "user_id": str(user.id),
            "name": preferred_name or user.full_name,
            "phone": user.phone,
            "completed_phase_ids": completed_phase_ids,
            "current_phase_id": compute_current_phase_id(
                phases=phase_dicts,
                completed_phase_ids=completed_phase_ids,
                trip_mode=settings["mode"],
                now=now,
                trip_end_date=settings["end_date"],
            ),
        })

    return {"trip_mode": settings["mode"], "phases": phase_dicts, "travelers": travelers}


async def get_trip_travelers(user_id: str, trip_id: str, session: AsyncSession) -> dict:
    await require_trip_membership(user_id, trip_id, session)
    positions = await _traveler_positions(trip_id, session)
    return {
        "travelers": [
            {
                "id": t["user_id"],
                "name": t["name"],
                "phone": t["phone"],
                "current_phase_id": t["current_phase_id"],
            }
            for t in positions["travelers"]
        ]
    }


async def get_traveler_locations(trip_uuid: str, session: AsyncSession) -> dict:
    """Staff view: each traveler's current phase/day, open pre-trip phases and last check-in.

    Callers must check staff access to the trip first.
    """
    from sqlalchemy import text as _text

    positions = await _traveler_positions(trip_uuid, session)
    phases_by_id = {p["id"]: p for p in positions["phases"]}
    pre_trip_ids = {p["id"] for p in positions["phases"] if p["phase_type"] == "pre-trip"}

    last_checkins: dict = {}
    tt_ids = [t["trip_traveler_id"] for t in positions["travelers"]]
    if tt_ids:
        result = await session.execute(
            _text("""
                SELECT DISTINCT ON (ac.trip_traveler_id)
                       ac.trip_traveler_id, ta.name AS activity_name,
                       tp.title AS day_title, ac.checked_in_at
                FROM activity_checkins ac
                JOIN trip_activities ta ON ta.id = ac.trip_activity_id
                JOIN trip_phases tp ON tp.id = ta.trip_phase_id
                WHERE ac.trip_traveler_id = ANY(:ids)
                  AND tp.wetravel_trip_uuid = :trip_uuid
                ORDER BY ac.trip_traveler_id, ac.checked_in_at DESC
            """),
            {"ids": tt_ids, "trip_uuid": trip_uuid},
        )
        for row in result.mappings():
            last_checkins[row["trip_traveler_id"]] = {
                "activity_name": row["activity_name"],
                "day_title": row["day_title"],
                "checked_in_at": row["checked_in_at"].isoformat() if row["checked_in_at"] else None,
            }

    travelers = []
    for t in positions["travelers"]:
        phase = phases_by_id.get(t["current_phase_id"])
        travelers.append({
            "id": str(t["trip_traveler_id"]),
            "name": t["name"],
            "phone": t["phone"],
            "current_phase": {
                "id": phase["id"],
                "title": phase["title"],
                "subtitle": phase["subtitle"],
                "phase_type": phase["phase_type"],
            } if phase else None,
            "pending_pre_trip": (
                len(pre_trip_ids - t["completed_phase_ids"])
                if positions["trip_mode"] == "in-trip" else 0
            ),
            "last_checkin": last_checkins.get(t["trip_traveler_id"]),
        })
    travelers.sort(key=lambda t: (t["name"] or "").lower())
    return {"trip_mode": positions["trip_mode"], "travelers": travelers}

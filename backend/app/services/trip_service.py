"""Trip service: fases, atividades e viajantes."""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime as _datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.trip import (
    TripActivity,
    TripPhase,
    TripPhaseChecklistItem,
    TripPhaseLink,
    TripTraveler,
)
from app.db.models.progress import TravelerPhaseProgress
from app.db.models.user import User

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


async def _get_trip_settings(trip_uuid: str, session: AsyncSession) -> dict:
    """Return mode and ideal_pace_phase_id for a trip. Defaults to pre-trip/None."""
    from sqlalchemy import text as _text
    result = await session.execute(
        _text("SELECT mode, ideal_pace_phase_id FROM trip_settings WHERE trip_uuid = :uuid"),
        {"uuid": trip_uuid},
    )
    row = result.mappings().first()
    if row:
        return {"mode": row["mode"], "ideal_pace_phase_id": row["ideal_pace_phase_id"]}
    return {"mode": "pre-trip", "ideal_pace_phase_id": None}


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
) -> str | None:
    if not phases:
        return None

    ordered_phases = sorted(phases, key=lambda p: p["sort_order"])

    if trip_mode == "in-trip":
        in_trip_phases = [p for p in ordered_phases if p["phase_type"] == "in-trip"]
        if in_trip_phases:
            if now.tzinfo is None:
                now = now.replace(tzinfo=UTC)
            today = now.astimezone(timezone).date()
            current_phase = in_trip_phases[0]

            for phase in in_trip_phases:
                phase_date = _phase_local_date(phase, timezone)
                if phase_date is not None and phase_date <= today:
                    current_phase = phase

            return current_phase["id"]

    for phase in ordered_phases:
        if phase["id"] not in completed_phase_ids:
            return phase["id"]
    return ordered_phases[-1]["id"]


async def _get_trip_uuid(user_id: str, session: AsyncSession) -> str:
    """Return the user's next active trip uuid."""
    try:
        _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

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
        raise HTTPException(status_code=404, detail="Viagem não encontrada para este usuário")
    return row["wetravel_trip_uuid"]


async def get_trip_phases(user_id: str, session: AsyncSession) -> dict:
    trip_uuid = await _get_trip_uuid(user_id, session)

    phases_result = await session.execute(
        select(TripPhase)
        .where(TripPhase.wetravel_trip_uuid == trip_uuid, TripPhase.is_visible.is_(True))
        .order_by(TripPhase.sort_order)
    )
    phases = phases_result.scalars().all()

    if not phases:
        trip_mode = await _get_trip_mode(trip_uuid, session)
        return {"wetravel_trip_uuid": trip_uuid, "trip_mode": trip_mode, "phases": []}

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
    return {
        "wetravel_trip_uuid": trip_uuid,
        "trip_mode": settings["mode"],
        "ideal_pace_phase_id": settings["ideal_pace_phase_id"],
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


async def get_trip_phase_detail(user_id: str, phase_id: str, session: AsyncSession) -> dict:
    trip_uuid = await _get_trip_uuid(user_id, session)

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


async def get_trip_travelers(user_id: str, session: AsyncSession) -> dict:
    trip_uuid = await _get_trip_uuid(user_id, session)

    tt_result = await session.execute(
        select(TripTraveler, User)
        .join(User, User.id == TripTraveler.user_id)
        .where(
            TripTraveler.wetravel_trip_uuid == trip_uuid,
            User.role == "traveler",
        )
    )
    rows = tt_result.all()

    if not rows:
        return {"travelers": []}

    tt_ids = [tt.id for tt, _ in rows]

    all_phases_result = await session.execute(
        select(TripPhase)
        .where(TripPhase.wetravel_trip_uuid == trip_uuid, TripPhase.is_visible.is_(True))
        .order_by(TripPhase.sort_order)
    )
    all_phases = all_phases_result.scalars().all()

    phase_dicts = [
        {
            "id": str(p.id),
            "phase_type": p.phase_type,
            "starts_at": p.starts_at,
            "sort_order": p.sort_order,
        }
        for p in all_phases
    ]
    now = _datetime.now(UTC)
    date_completions = compute_in_trip_phase_completions(phase_dicts, now)
    settings = await _get_trip_settings(trip_uuid, session)

    progress_result = await session.execute(
        select(TravelerPhaseProgress)
        .where(
            TravelerPhaseProgress.trip_traveler_id.in_(tt_ids),
            TravelerPhaseProgress.is_completed.is_(True),
        )
    )
    db_completed_ids: dict[_uuid.UUID, set[str]] = {}
    for prog in progress_result.scalars():
        db_completed_ids.setdefault(prog.trip_traveler_id, set()).add(str(prog.trip_phase_id))

    travelers = []
    for tt, user in rows:
        completed_phase_ids = db_completed_ids.get(tt.id, set()) | {
            pid for pid, is_completed in date_completions.items() if is_completed
        }
        travelers.append({
            "id": str(user.id),
            "name": user.full_name,
            "phone": user.phone,
            "current_phase_id": compute_current_phase_id(
                phases=phase_dicts,
                completed_phase_ids=completed_phase_ids,
                trip_mode=settings["mode"],
                now=now,
            ),
        })

    return {"travelers": travelers}

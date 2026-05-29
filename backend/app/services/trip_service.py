"""Trip service: fases, atividades e viajantes."""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime as _datetime

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
from app.db.models.progress import TravelerPhaseProgress
from app.db.models.user import User


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


async def _get_trip_uuid(user_id: str, session: AsyncSession) -> str:
    """Retorna o wetravel_trip_uuid do primeiro trip do usuário."""
    try:
        uid = _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    tt = await session.scalar(
        select(TripTraveler).where(TripTraveler.user_id == uid).limit(1)
    )
    if not tt:
        raise HTTPException(status_code=404, detail="Viagem não encontrada para este usuário")
    return tt.wetravel_trip_uuid


async def get_trip_phases(user_id: str, session: AsyncSession) -> dict:
    trip_uuid = await _get_trip_uuid(user_id, session)

    phases_result = await session.execute(
        select(TripPhase)
        .where(TripPhase.wetravel_trip_uuid == trip_uuid, TripPhase.is_visible.is_(True))
        .order_by(TripPhase.sort_order)
    )
    phases = phases_result.scalars().all()

    if not phases:
        return {"wetravel_trip_uuid": trip_uuid, "phases": []}

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

    return {
        "wetravel_trip_uuid": trip_uuid,
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
        .where(TripTraveler.wetravel_trip_uuid == trip_uuid)
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
    phases_ordered = [(p["sort_order"], p["id"]) for p in phase_dicts]

    now = _datetime.now(UTC)
    date_completions = compute_in_trip_phase_completions(phase_dicts, now)

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

    def _current_phase_id(tt_id: _uuid.UUID) -> str | None:
        if not phases_ordered:
            return None
        tt_db_done = db_completed_ids.get(tt_id, set())
        # Pre-trip phases complete via DB only; in-trip phases complete by date.
        # If the trip has started but the traveler never finished pre-trip,
        # they remain on the last incomplete pre-trip phase by design.
        for sort_order, pid in phases_ordered:
            is_done = (pid in tt_db_done) or date_completions.get(pid, False)
            if not is_done:
                return pid
        return phases_ordered[-1][1]

    travelers = []
    for tt, user in rows:
        travelers.append({
            "id": str(user.id),
            "name": user.full_name,
            "phone": user.phone,
            "current_phase_id": _current_phase_id(tt.id),
        })

    return {"travelers": travelers}

"""Trip service: fases, atividades e viajantes."""

from __future__ import annotations

import uuid as _uuid

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

    # Busca todos os travelers do mesmo trip
    tt_result = await session.execute(
        select(TripTraveler, User)
        .join(User, User.id == TripTraveler.user_id)
        .where(TripTraveler.wetravel_trip_uuid == trip_uuid)
    )
    rows = tt_result.all()

    if not rows:
        return {"travelers": []}

    tt_ids = [tt.id for tt, _ in rows]

    # Fase atual = primeira fase NÃO completada (menor sort_order)
    first_phase = await session.scalar(
        select(TripPhase)
        .where(TripPhase.wetravel_trip_uuid == trip_uuid, TripPhase.is_visible.is_(True))
        .order_by(TripPhase.sort_order)
        .limit(1)
    )
    first_phase_id = str(first_phase.id) if first_phase else None

    # Carrega progresso de todos os travelers de uma vez
    progress_result = await session.execute(
        select(TravelerPhaseProgress, TripPhase)
        .join(TripPhase, TripPhase.id == TravelerPhaseProgress.trip_phase_id)
        .where(
            TravelerPhaseProgress.trip_traveler_id.in_(tt_ids),
            TravelerPhaseProgress.is_completed.is_(True),
        )
        .order_by(TravelerPhaseProgress.trip_traveler_id, TripPhase.sort_order)
    )
    completed_by_tt: dict[_uuid.UUID, int] = {}
    for prog, phase in progress_result.all():
        # Guarda o maior sort_order completado por traveler
        current = completed_by_tt.get(prog.trip_traveler_id, -1)
        if phase.sort_order > current:
            completed_by_tt[prog.trip_traveler_id] = phase.sort_order

    # Para calcular "current phase" precisamos das fases ordenadas
    all_phases_result = await session.execute(
        select(TripPhase)
        .where(TripPhase.wetravel_trip_uuid == trip_uuid, TripPhase.is_visible.is_(True))
        .order_by(TripPhase.sort_order)
    )
    all_phases = all_phases_result.scalars().all()
    phases_ordered = [(p.sort_order, str(p.id)) for p in all_phases]

    def _current_phase_id(tt_id: _uuid.UUID) -> str | None:
        if not phases_ordered:
            return None
        max_completed = completed_by_tt.get(tt_id, -1)
        # Próxima fase após a última completada
        for sort_order, pid in phases_ordered:
            if sort_order > max_completed:
                return pid
        # Todas completadas → última fase
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

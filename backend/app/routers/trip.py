"""Trip HTTP routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.trip_service import (
    get_trip_phase_detail,
    get_trip_phases,
    get_trip_travelers,
)

router = APIRouter(tags=["trip"])


@router.get("/me/trip")
async def get_my_trip(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the authenticated traveler's active trip info."""
    user_id = request.state.user_id

    result = await session.execute(
        text("""
            SELECT
                tt.wetravel_trip_uuid,
                wt.title,
                wt.destination,
                wt.start_date,
                wt.end_date,
                wt.url,
                wt.service_agreement_url
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
        return {"trip": None}

    from app.services.trip_service import _get_trip_mode
    trip_uuid = row["wetravel_trip_uuid"]
    trip_mode = await _get_trip_mode(trip_uuid, session)
    return {
        "trip": {
            "wetravel_trip_uuid": trip_uuid,
            "title": row["title"],
            "destination": row["destination"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "url": row["url"],
            "service_agreement_url": row["service_agreement_url"],
            "trip_mode": trip_mode,
        }
    }


@router.get("/me/trip/phases")
async def get_my_trip_phases(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Retorna todas as fases da viagem do usuário autenticado."""
    return await get_trip_phases(request.state.user_id, session)


@router.get("/me/trip/phases/{phase_id}")
async def get_my_trip_phase_detail(
    phase_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Retorna uma fase específica com atividades."""
    return await get_trip_phase_detail(request.state.user_id, phase_id, session)


@router.get("/me/trip/travelers")
async def get_my_trip_travelers(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Retorna todos os viajantes do mesmo trip com fase atual de cada um."""
    return await get_trip_travelers(request.state.user_id, session)

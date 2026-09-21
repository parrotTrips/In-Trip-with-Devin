"""Console HTTP routes — requires JWT with role=admin."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.console import PhaseCreate
from app.services.console_service import (
    create_phase,
    get_phases,
    list_trips,
    require_admin,
)

router = APIRouter(prefix="/console", tags=["console"])


@router.get("/trips")
async def list_trips_handler(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return active trips available for content editing."""
    await require_admin(request, session)
    return await list_trips(session)


@router.get("/trips/{trip_uuid}/phases")
async def get_phases_handler(
    trip_uuid: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return pre-trip phases with checklist items and links."""
    await require_admin(request, session)
    return await get_phases(session, trip_uuid)


@router.post("/trips/{trip_uuid}/phases")
async def create_phase_handler(
    trip_uuid: str,
    body: PhaseCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Create a pre-trip phase in draft state."""
    await require_admin(request, session)
    return await create_phase(session, trip_uuid, body.model_dump())

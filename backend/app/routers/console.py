"""Console HTTP routes — requires JWT with role=admin."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.console_service import get_phases, list_trips, require_admin

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

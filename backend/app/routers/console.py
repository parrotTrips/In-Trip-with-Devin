"""Console HTTP routes — requires JWT with role=admin."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.console import (
    ChecklistReplace,
    LinkReplace,
    PhaseCreate,
    PhaseOrder,
    PhaseUpdate,
)
from app.services.console_service import (
    create_phase,
    delete_phase,
    get_phases,
    list_trips,
    reorder_phases,
    replace_checklist,
    replace_links,
    require_admin,
    set_phase_visibility,
    update_phase,
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


@router.patch("/phases/{phase_id}")
async def update_phase_handler(
    phase_id: str,
    body: PhaseUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Update phase fields."""
    await require_admin(request, session)
    return await update_phase(session, phase_id, body.model_dump(exclude_unset=True))


@router.post("/phases/{phase_id}/publish")
async def publish_phase_handler(
    phase_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Make the phase visible to travelers and staff."""
    await require_admin(request, session)
    return await set_phase_visibility(session, phase_id, True)


@router.post("/phases/{phase_id}/unpublish")
async def unpublish_phase_handler(
    phase_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the phase to draft state."""
    await require_admin(request, session)
    return await set_phase_visibility(session, phase_id, False)


@router.delete("/phases/{phase_id}")
async def delete_phase_handler(
    phase_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a phase and its checklist items and links."""
    await require_admin(request, session)
    return await delete_phase(session, phase_id)


@router.put("/phases/{phase_id}/checklist")
async def replace_checklist_handler(
    phase_id: str,
    body: ChecklistReplace,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Replace the phase checklist with the list sent, in order."""
    await require_admin(request, session)
    return await replace_checklist(session, phase_id, [i.model_dump() for i in body.items])


@router.put("/phases/{phase_id}/links")
async def replace_links_handler(
    phase_id: str,
    body: LinkReplace,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Replace the phase links with the list sent, in order."""
    await require_admin(request, session)
    return await replace_links(session, phase_id, [link.model_dump() for link in body.links])


@router.put("/trips/{trip_uuid}/phases/order")
async def reorder_phases_handler(
    trip_uuid: str,
    body: PhaseOrder,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Reorder the trip phases according to the list sent."""
    await require_admin(request, session)
    return await reorder_phases(session, trip_uuid, body.phase_ids)

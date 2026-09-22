"""Console HTTP routes — requires JWT with role=admin."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.console_auth import require_console_access
from app.db.session import get_db_session
from app.schemas.console import (
    ChecklistReplace,
    LinkReplace,
    PhaseContentUpdate,
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
    save_phase_content,
    set_phase_visibility,
    update_phase,
)

router = APIRouter(
    prefix="/console",
    tags=["console"],
    dependencies=[Depends(require_console_access)],
)


@router.get("/trips")
async def list_trips_handler(
    session: AsyncSession = Depends(get_db_session),
):
    """Return active trips available for content editing."""
    return await list_trips(session)


@router.get("/trips/{trip_uuid}/phases")
async def get_phases_handler(
    trip_uuid: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Return pre-trip phases with checklist items and links."""
    return await get_phases(session, trip_uuid)


@router.post("/trips/{trip_uuid}/phases")
async def create_phase_handler(
    trip_uuid: str,
    body: PhaseCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """Create a pre-trip phase in draft state."""
    return await create_phase(session, trip_uuid, body.model_dump())


@router.patch("/phases/{phase_id}")
async def update_phase_handler(
    phase_id: str,
    body: PhaseUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """Update phase fields."""
    return await update_phase(session, phase_id, body.model_dump(exclude_unset=True))


@router.put("/phases/{phase_id}/content")
async def save_phase_content_handler(
    phase_id: str,
    body: PhaseContentUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """Atomically replace all editable content of one draft phase."""
    return await save_phase_content(session, phase_id, body.model_dump())


@router.post("/phases/{phase_id}/publish")
async def publish_phase_handler(
    phase_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Make the phase visible to travelers and staff."""
    return await set_phase_visibility(session, phase_id, True)


@router.post("/phases/{phase_id}/unpublish")
async def unpublish_phase_handler(
    phase_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the phase to draft state."""
    return await set_phase_visibility(session, phase_id, False)


@router.delete("/phases/{phase_id}")
async def delete_phase_handler(
    phase_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a phase and its checklist items and links."""
    return await delete_phase(session, phase_id)


@router.put("/phases/{phase_id}/checklist")
async def replace_checklist_handler(
    phase_id: str,
    body: ChecklistReplace,
    session: AsyncSession = Depends(get_db_session),
):
    """Replace the phase checklist with the list sent, in order."""
    return await replace_checklist(session, phase_id, [i.model_dump() for i in body.items])


@router.put("/phases/{phase_id}/links")
async def replace_links_handler(
    phase_id: str,
    body: LinkReplace,
    session: AsyncSession = Depends(get_db_session),
):
    """Replace the phase links with the list sent, in order."""
    return await replace_links(
        session, phase_id, [link.model_dump(mode="json") for link in body.links]
    )


@router.put("/trips/{trip_uuid}/phases/order")
async def reorder_phases_handler(
    trip_uuid: str,
    body: PhaseOrder,
    session: AsyncSession = Depends(get_db_session),
):
    """Reorder the trip phases according to the list sent."""
    return await reorder_phases(session, trip_uuid, body.phase_ids)

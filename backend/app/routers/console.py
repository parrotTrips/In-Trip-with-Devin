"""Console HTTP routes protected by Google Workspace authentication."""

from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.console_auth import require_console_access
from app.db.session import get_db_session
from app.schemas.console import (
    ActivityIn,
    ActivityOrder,
    ChecklistReplace,
    DayCreate,
    SectionReplace,
    LinkReplace,
    PhaseContentUpdate,
    PhaseCreate,
    PhaseOrder,
    PhaseUpdate,
)
from app.services.console_roteiro import (
    create_activity,
    delete_activity,
    get_days,
    reorder_activities,
    update_activity,
)
from app.services.console_sections import (
    get_section_rows,
    list_sections,
    replace_section,
)
from app.services.console_service import (
    create_phase,
    create_wrap_up_phase,
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


# Phases edited on the phases screens; in-trip days have their own Roteiro routes.
EditablePhaseType = Literal["pre-trip", "post-trip"]


@router.get("/trips/{trip_uuid}/phases")
async def get_phases_handler(
    trip_uuid: str,
    phase_type: EditablePhaseType = "pre-trip",
    session: AsyncSession = Depends(get_db_session),
):
    """Return pre-trip (or Trip Wrap-up) phases with checklist items and links."""
    return await get_phases(session, trip_uuid, phase_type)


@router.post("/trips/{trip_uuid}/phases")
async def create_phase_handler(
    trip_uuid: str,
    body: PhaseCreate,
    phase_type: EditablePhaseType = "pre-trip",
    session: AsyncSession = Depends(get_db_session),
):
    """Create a pre-trip (or Trip Wrap-up) phase in draft state."""
    return await create_phase(session, trip_uuid, body.model_dump(), phase_type)


@router.post("/trips/{trip_uuid}/wrap-up")
async def create_wrap_up_handler(
    trip_uuid: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Create the Trip Wrap-up phase from the default template, as a draft."""
    return await create_wrap_up_phase(session, trip_uuid)


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


@router.get("/trips/{trip_uuid}/sections")
async def list_sections_handler(
    trip_uuid: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Return every section of the trip with its group and row count."""
    return await list_sections(session, trip_uuid)


@router.get("/trips/{trip_uuid}/sections/{section_key}")
async def get_section_handler(
    trip_uuid: str,
    section_key: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the rows of one read-only section."""
    return await get_section_rows(session, trip_uuid, section_key)


@router.put("/trips/{trip_uuid}/sections/{section_key}")
async def replace_section_handler(
    trip_uuid: str,
    section_key: str,
    body: SectionReplace,
    session: AsyncSession = Depends(get_db_session),
):
    """Replace the rows of an editable section with the list sent, in order."""
    return await replace_section(session, trip_uuid, section_key, body.items)


@router.get("/trips/{trip_uuid}/days")
async def get_days_handler(
    trip_uuid: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Return in-trip days with their activities."""
    return await get_days(session, trip_uuid)


@router.post("/trips/{trip_uuid}/days")
async def create_day_handler(
    trip_uuid: str,
    body: DayCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """Create an in-trip day. A day is a phase, so it reuses the phase creation."""
    payload = {
        "subtitle": None,
        "icon": None,
        "detailed_description": None,
        **body.model_dump(),
    }
    return await create_phase(session, trip_uuid, payload, phase_type="in-trip")


@router.post("/days/{day_id}/activities")
async def create_activity_handler(
    day_id: str,
    body: ActivityIn,
    session: AsyncSession = Depends(get_db_session),
):
    """Append an activity to a day."""
    return await create_activity(session, day_id, body.model_dump(exclude_unset=True, mode="json"))


@router.patch("/activities/{activity_id}")
async def update_activity_handler(
    activity_id: str,
    body: ActivityIn,
    session: AsyncSession = Depends(get_db_session),
):
    """Update an activity in place, preserving its check-ins."""
    return await update_activity(
        session, activity_id, body.model_dump(exclude_unset=True, mode="json")
    )


@router.delete("/activities/{activity_id}")
async def delete_activity_handler(
    activity_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Delete an activity, refusing when attendance records depend on it."""
    return await delete_activity(session, activity_id)


@router.put("/days/{day_id}/activities/order")
async def reorder_activities_handler(
    day_id: str,
    body: ActivityOrder,
    session: AsyncSession = Depends(get_db_session),
):
    """Reorder the activities of a day."""
    return await reorder_activities(session, day_id, body.activity_ids)

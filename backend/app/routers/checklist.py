"""Checklist and phase completion HTTP routes."""

from fastapi import APIRouter

from app.schemas.checklist import ChecklistUpdate, PhaseCompletionUpdate
from app.services.checklist_service import (
    get_checklist_progress,
    get_phase_completions,
    update_checklist_item,
    update_phase_completion,
)

router = APIRouter(tags=["checklist"])


@router.post("/checklist/update")
async def update_checklist_item_handler(user_id: int, update: ChecklistUpdate):
    """Persist one checklist item state."""
    return await update_checklist_item(user_id, update.model_dump())


@router.get("/checklist/{trip_id}/{user_id}")
async def get_checklist_progress_handler(trip_id: str, user_id: int):
    """Return checklist progress grouped by phase and item."""
    return await get_checklist_progress(trip_id, user_id)


@router.post("/phases/complete")
async def update_phase_completion_handler(user_id: int, update: PhaseCompletionUpdate):
    """Persist one phase completion state."""
    return await update_phase_completion(user_id, update.model_dump())


@router.get("/phases/{trip_id}/{user_id}")
async def get_phase_completions_handler(trip_id: str, user_id: int):
    """Return phase completion flags for one traveler."""
    return await get_phase_completions(trip_id, user_id)

"""Checklist and phase completion HTTP routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.checklist import ChecklistUpdate, PhaseCompletionUpdate
from app.services.checklist_service import (
    get_checklist_progress,
    get_phase_completions,
    update_checklist_item,
    update_phase_completion,
)

router = APIRouter(tags=["checklist"])


def _require_matching_session(user_id: str, trip_id: str, request: Request) -> None:
    """The session (selected trip + authenticated user) is the source of truth.

    Caller-supplied user_id/trip_id are kept for frontend compatibility but must
    match the authenticated session, else 403.
    """
    if user_id != request.state.user_id:
        raise HTTPException(status_code=403, detail="User mismatch")
    if trip_id != request.state.trip_id:
        raise HTTPException(status_code=403, detail="Trip mismatch")


@router.post("/checklist/update")
async def update_checklist_item_handler(
    user_id: str,
    update: ChecklistUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Persist one checklist item state."""
    _require_matching_session(user_id, update.trip_id, request)
    return await update_checklist_item(user_id, update.model_dump(), session)


@router.get("/checklist/{trip_id}/{user_id}")
async def get_checklist_progress_handler(
    trip_id: str,
    user_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return checklist progress grouped by phase and item."""
    _require_matching_session(user_id, trip_id, request)
    return await get_checklist_progress(trip_id, user_id, session)


@router.post("/phases/complete")
async def update_phase_completion_handler(
    user_id: str,
    update: PhaseCompletionUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Persist one phase completion state."""
    _require_matching_session(user_id, update.trip_id, request)
    return await update_phase_completion(user_id, update.model_dump(), session)


@router.get("/phases/{trip_id}/{user_id}")
async def get_phase_completions_handler(
    trip_id: str,
    user_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return phase completion flags for one traveler."""
    _require_matching_session(user_id, trip_id, request)
    return await get_phase_completions(trip_id, user_id, session)

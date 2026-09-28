"""Profile HTTP routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.profile import ProfileUpdate
from app.services.profile_service import get_profile, get_trip_travelers, update_profile

router = APIRouter(tags=["profile"])


def _require_matching_user(user_id: str, request: Request) -> None:
    if user_id != request.state.user_id:
        raise HTTPException(status_code=403, detail="User mismatch")


def _require_matching_trip(trip_id: Optional[str], request: Request) -> str:
    """The session's selected trip is the source of truth.

    A caller-supplied `trip_id` (kept for frontend compatibility) must match it.
    """
    if trip_id is not None and trip_id != request.state.trip_id:
        raise HTTPException(status_code=403, detail="Trip mismatch")
    return request.state.trip_id


@router.get("/profile/{user_id}")
async def get_profile_handler(
    user_id: str,
    request: Request,
    trip_id: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the persisted profile payload for one traveler."""
    _require_matching_user(user_id, request)
    scoped_trip_id = _require_matching_trip(trip_id, request)
    return await get_profile(user_id, scoped_trip_id, session)


@router.put("/profile/{user_id}")
async def update_profile_handler(
    user_id: str,
    update: ProfileUpdate,
    request: Request,
    trip_id: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
):
    """Create or update the persisted traveler profile."""
    _require_matching_user(user_id, request)
    scoped_trip_id = _require_matching_trip(trip_id, request)
    return await update_profile(user_id, scoped_trip_id, update.model_dump(), session)


@router.get("/trip/{trip_id}/travelers")
async def get_trip_travelers_handler(
    trip_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """List travelers used by the roommate selection flow."""
    _require_matching_trip(trip_id, request)
    return await get_trip_travelers(trip_id, session)

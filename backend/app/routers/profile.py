"""Profile HTTP routes."""

from fastapi import APIRouter

from app.schemas.profile import ProfileUpdate
from app.services.profile_service import get_profile, get_trip_travelers, update_profile

router = APIRouter(tags=["profile"])


@router.get("/profile/{user_id}")
async def get_profile_handler(user_id: int):
    """Return the persisted profile payload for one traveler."""
    return await get_profile(user_id)


@router.put("/profile/{user_id}")
async def update_profile_handler(user_id: int, update: ProfileUpdate):
    """Create or update the persisted traveler profile."""
    return await update_profile(user_id, update.model_dump())


@router.get("/trip/{trip_id}/travelers")
async def get_trip_travelers_handler(trip_id: str):
    """List travelers used by the roommate selection flow."""
    return await get_trip_travelers(trip_id)

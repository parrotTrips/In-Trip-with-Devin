"""User HTTP routes."""

from fastapi import APIRouter

from app.schemas.users import UserUpdate
from app.services.user_service import get_user, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/{user_id}")
async def update_user_handler(user_id: int, update: UserUpdate):
    """Update editable user fields."""
    return await update_user(user_id, update.model_dump())


@router.get("/{user_id}")
async def get_user_handler(user_id: int):
    """Return one user by identifier."""
    return await get_user(user_id)

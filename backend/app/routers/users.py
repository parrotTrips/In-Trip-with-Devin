"""User HTTP routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.users import UserUpdate
from app.services.user_service import get_user, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/{user_id}")
async def update_user_handler(
    user_id: str,
    update: UserUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """Update editable user fields."""
    return await update_user(user_id, update.model_dump(), session)


@router.get("/{user_id}")
async def get_user_handler(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Return one user by identifier."""
    return await get_user(user_id, session)

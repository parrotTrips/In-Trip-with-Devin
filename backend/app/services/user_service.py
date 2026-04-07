"""User service functions."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


def _parse_user_id(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


async def update_user(
    user_id: str,
    update: dict,
    session: AsyncSession,
) -> dict:
    """Persist editable user fields without changing the HTTP contract."""
    user = await session.scalar(select(User).where(User.id == _parse_user_id(user_id)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update.get("name") is not None:
        user.full_name = update["name"]

    await session.commit()

    return {"message": "User updated"}


async def get_user(user_id: str, session: AsyncSession) -> dict:
    """Fetch one user and raise the same 404 used by the existing API."""
    user = await session.scalar(select(User).where(User.id == _parse_user_id(user_id)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "phone": user.phone,
        "name": user.full_name,
    }

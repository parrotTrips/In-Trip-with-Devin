"""User service functions."""

from __future__ import annotations

from pathlib import Path

import aiosqlite
from fastapi import HTTPException

from app.db.database import connect_to_database


async def update_user(
    user_id: int,
    update: dict,
    database_path: str | Path | None = None,
) -> dict:
    """Persist editable user fields without changing the HTTP contract."""
    async with connect_to_database(database_path) as db:
        if update.get("name") is not None:
            await db.execute(
                "UPDATE users SET name = ? WHERE id = ?",
                (update["name"], user_id),
            )
        await db.commit()

    return {"message": "User updated"}


async def get_user(user_id: int, database_path: str | Path | None = None) -> dict:
    """Fetch one user and raise the same 404 used by the existing API."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user["id"],
        "phone": user["phone"],
        "name": user["name"],
    }

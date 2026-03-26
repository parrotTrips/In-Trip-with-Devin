"""Profile service functions."""

from __future__ import annotations

from pathlib import Path

import aiosqlite
from fastapi import HTTPException

from app.db.database import connect_to_database


async def get_profile(user_id: int, database_path: str | Path | None = None) -> dict:
    """Return one traveler profile together with the linked basic user data."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        profile = await cursor.fetchone()

        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        roommate_info = None
        if profile and profile["roommate_user_id"]:
            cursor = await db.execute(
                "SELECT id, name, phone FROM users WHERE id = ?",
                (profile["roommate_user_id"],),
            )
            roommate = await cursor.fetchone()
            if roommate:
                roommate_info = {
                    "id": roommate["id"],
                    "name": roommate["name"],
                    "phone": roommate["phone"],
                }

        if not profile:
            return {
                "user_id": user_id,
                "phone": user["phone"],
                "name": user["name"],
                "profile": None,
                "roommate": roommate_info,
            }

        profile_dict = {
            key: profile[key]
            for key in profile.keys()
            if key not in ("id", "user_id", "trip_id", "updated_at")
        }
        return {
            "user_id": user_id,
            "phone": user["phone"],
            "name": user["name"],
            "profile": profile_dict,
            "roommate": roommate_info,
        }


async def update_profile(
    user_id: int,
    update: dict,
    database_path: str | Path | None = None,
) -> dict:
    """Create or update a traveler profile while preserving current responses."""
    async with connect_to_database(database_path) as db:
        cursor = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        cursor = await db.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
        existing = await cursor.fetchone()

        update_data = {key: value for key, value in update.items() if value is not None}
        if not update_data:
            return {"message": "No fields to update"}

        if existing:
            set_clauses = ", ".join(f"{key} = ?" for key in update_data)
            values = list(update_data.values()) + [user_id]
            await db.execute(
                f"UPDATE user_profiles SET {set_clauses}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                values,
            )
        else:
            insert_data = {"user_id": user_id, **update_data}
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join("?" for _ in insert_data)
            await db.execute(
                f"INSERT INTO user_profiles ({columns}) VALUES ({placeholders})",
                list(insert_data.values()),
            )

        if update_data.get("preferred_name"):
            await db.execute(
                "UPDATE users SET name = ? WHERE id = ?",
                (update_data["preferred_name"], user_id),
            )

        await db.commit()

    return {"message": "Profile updated"}


async def get_trip_travelers(
    trip_id: str, database_path: str | Path | None = None
) -> dict:
    """List all travelers available for roommate selection in a trip."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, name, phone FROM users ORDER BY id")
        rows = await cursor.fetchall()

    return {
        "trip_id": trip_id,
        "travelers": [
            {"id": row["id"], "name": row["name"], "phone": row["phone"]}
            for row in rows
        ],
    }

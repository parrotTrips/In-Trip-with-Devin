"""Mission service functions."""

from __future__ import annotations

from pathlib import Path

import aiosqlite
from fastapi import HTTPException

from app.db.database import connect_to_database


async def get_missions(
    trip_id: str,
    user_id: int | None = None,
    database_path: str | Path | None = None,
) -> dict:
    """Return all active missions for a trip with optional user completion state."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM missions WHERE trip_id = ? AND active = TRUE ORDER BY sort_order",
            (trip_id,),
        )
        missions = await cursor.fetchall()

        completed_ids: set[int] = set()
        if user_id:
            cursor = await db.execute(
                "SELECT mission_id FROM mission_completions WHERE user_id = ?",
                (user_id,),
            )
            completed_ids = {row["mission_id"] for row in await cursor.fetchall()}

    return {
        "trip_id": trip_id,
        "missions": [
            {
                "id": mission["id"],
                "title": mission["title"],
                "description": mission["description"],
                "points": mission["points"],
                "icon": mission["icon"],
                "category": mission["category"],
                "completed": mission["id"] in completed_ids,
            }
            for mission in missions
        ],
    }


async def complete_mission(
    trip_id: str,
    user_id: int,
    mission_id: int,
    database_path: str | Path | None = None,
) -> dict:
    """Persist one mission completion and return the existing response payload."""
    async with connect_to_database(database_path) as db:
        cursor = await db.execute(
            "SELECT id, points, title FROM missions WHERE id = ? AND trip_id = ?",
            (mission_id, trip_id),
        )
        mission = await cursor.fetchone()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        cursor = await db.execute(
            "SELECT id FROM mission_completions WHERE user_id = ? AND mission_id = ?",
            (user_id, mission_id),
        )
        if await cursor.fetchone():
            return {"message": "Mission already completed", "already_completed": True}

        await db.execute(
            "INSERT INTO mission_completions (user_id, mission_id) VALUES (?, ?)",
            (user_id, mission_id),
        )
        await db.commit()

    return {
        "message": "Mission completed!",
        "points_earned": mission[1],
        "already_completed": False,
    }


async def uncomplete_mission(
    trip_id: str,
    user_id: int,
    mission_id: int,
    database_path: str | Path | None = None,
) -> dict:
    """Remove one persisted mission completion for a user."""
    async with connect_to_database(database_path) as db:
        await db.execute(
            "DELETE FROM mission_completions WHERE user_id = ? AND mission_id = ?",
            (user_id, mission_id),
        )
        await db.commit()

    return {"message": "Mission uncompleted"}


async def get_leaderboard(
    trip_id: str, database_path: str | Path | None = None
) -> dict:
    """Return the mission points leaderboard for a trip."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT u.id, u.name, u.phone,
                   COALESCE(SUM(m.points), 0) as total_points,
                   COUNT(mc.id) as missions_completed
            FROM users u
            LEFT JOIN mission_completions mc ON u.id = mc.user_id
            LEFT JOIN missions m ON mc.mission_id = m.id AND m.trip_id = ?
            GROUP BY u.id
            ORDER BY total_points DESC
            """,
            (trip_id,),
        )
        rows = await cursor.fetchall()

    return {
        "trip_id": trip_id,
        "leaderboard": [
            {
                "user_id": row["id"],
                "name": row["name"] or row["phone"],
                "total_points": row["total_points"],
                "missions_completed": row["missions_completed"],
            }
            for row in rows
        ],
    }


async def get_user_points(
    trip_id: str,
    user_id: int,
    database_path: str | Path | None = None,
) -> dict:
    """Return the total mission points and completion count for one user."""
    async with connect_to_database(database_path) as db:
        cursor = await db.execute(
            """
            SELECT COALESCE(SUM(m.points), 0) as total_points,
                   COUNT(mc.id) as missions_completed
            FROM mission_completions mc
            JOIN missions m ON mc.mission_id = m.id
            WHERE mc.user_id = ? AND m.trip_id = ?
            """,
            (user_id, trip_id),
        )
        row = await cursor.fetchone()

    return {
        "user_id": user_id,
        "total_points": row[0] if row else 0,
        "missions_completed": row[1] if row else 0,
    }


async def create_mission(
    mission: dict, database_path: str | Path | None = None
) -> dict:
    """Create one mission using the current admin endpoint contract."""
    async with connect_to_database(database_path) as db:
        await db.execute(
            """
            INSERT INTO missions (trip_id, title, description, points, icon, category, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mission["trip_id"],
                mission["title"],
                mission["description"],
                mission["points"],
                mission["icon"],
                mission["category"],
                mission["sort_order"],
            ),
        )
        await db.commit()

    return {"message": "Mission created"}

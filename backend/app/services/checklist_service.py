"""Checklist and phase completion service functions."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

from app.db.database import connect_to_database


async def update_checklist_item(
    user_id: int,
    update: dict,
    database_path: str | Path | None = None,
) -> dict:
    """Persist one checklist item completion state for a user."""
    async with connect_to_database(database_path) as db:
        await db.execute(
            """
            INSERT INTO checklist_progress (user_id, trip_id, phase_id, item_id, completed, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, trip_id, phase_id, item_id)
            DO UPDATE SET completed = ?, updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                update["trip_id"],
                update["phase_id"],
                update["item_id"],
                update["completed"],
                update["completed"],
            ),
        )
        await db.commit()

    return {"message": "Checklist item updated"}


async def get_checklist_progress(
    trip_id: str,
    user_id: int,
    database_path: str | Path | None = None,
) -> dict:
    """Return all persisted checklist progress for one user and trip."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT phase_id, item_id, completed FROM checklist_progress WHERE user_id = ? AND trip_id = ?",
            (user_id, trip_id),
        )
        rows = await cursor.fetchall()

    progress: dict[str, dict[str, bool]] = {}
    for row in rows:
        phase_id = row["phase_id"]
        progress.setdefault(phase_id, {})[row["item_id"]] = bool(row["completed"])

    return {"trip_id": trip_id, "user_id": user_id, "progress": progress}


async def update_phase_completion(
    user_id: int,
    update: dict,
    database_path: str | Path | None = None,
) -> dict:
    """Persist one phase completion state for a user."""
    async with connect_to_database(database_path) as db:
        await db.execute(
            """
            INSERT INTO phase_completion (user_id, trip_id, phase_id, completed, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, trip_id, phase_id)
            DO UPDATE SET completed = ?, updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                update["trip_id"],
                update["phase_id"],
                update["completed"],
                update["completed"],
            ),
        )
        await db.commit()

    return {"message": "Phase completion updated"}


async def get_phase_completions(
    trip_id: str,
    user_id: int,
    database_path: str | Path | None = None,
) -> dict:
    """Return all persisted phase completion states for one user and trip."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT phase_id, completed FROM phase_completion WHERE user_id = ? AND trip_id = ?",
            (user_id, trip_id),
        )
        rows = await cursor.fetchall()

    completions = {row["phase_id"]: bool(row["completed"]) for row in rows}
    return {"trip_id": trip_id, "user_id": user_id, "completions": completions}

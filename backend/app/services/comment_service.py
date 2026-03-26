"""Comment service functions."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

from app.db.database import connect_to_database


async def add_comment(
    user_id: int,
    comment: dict,
    database_path: str | Path | None = None,
) -> dict:
    """Persist a phase comment using the current public API contract."""
    async with connect_to_database(database_path) as db:
        await db.execute(
            """
            INSERT INTO comments (user_id, trip_id, phase_id, text, is_private)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                comment["trip_id"],
                comment["phase_id"],
                comment["text"],
                comment["is_private"],
            ),
        )
        await db.commit()

    return {"message": "Comment added"}


async def get_comments(
    trip_id: str,
    phase_id: str,
    database_path: str | Path | None = None,
) -> dict:
    """Return all public comments for one trip phase."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT c.id, c.text, c.created_at, c.is_private,
                   u.id as user_id, u.name as user_name, u.phone as user_phone
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.trip_id = ? AND c.phase_id = ? AND c.is_private = FALSE
            ORDER BY c.created_at ASC
            """,
            (trip_id, phase_id),
        )
        rows = await cursor.fetchall()

    comments_list = [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "user_name": row["user_name"] or row["user_phone"],
            "text": row["text"],
            "created_at": row["created_at"],
            "is_private": bool(row["is_private"]),
        }
        for row in rows
    ]
    return {"trip_id": trip_id, "phase_id": phase_id, "comments": comments_list}

"""Notification service functions."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

from app.db.database import connect_to_database


async def get_notifications(
    user_id: int,
    unread_only: bool = False,
    database_path: str | Path | None = None,
) -> dict:
    """Return notifications and unread count for one user."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM notifications WHERE user_id = ?"
        if unread_only:
            query += " AND read = FALSE"
        query += " ORDER BY created_at DESC LIMIT 50"
        cursor = await db.execute(query, (user_id,))
        rows = await cursor.fetchall()

    notifications = [
        {
            "id": row["id"],
            "title": row["title"],
            "body": row["body"],
            "type": row["type"],
            "link": row["link"],
            "read": bool(row["read"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    unread_count = sum(1 for row in rows if not row["read"])
    return {"notifications": notifications, "unread_count": unread_count}


async def get_unread_count(
    user_id: int, database_path: str | Path | None = None
) -> dict:
    """Return only the unread notification count for one user."""
    async with connect_to_database(database_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND read = FALSE",
            (user_id,),
        )
        row = await cursor.fetchone()

    return {"unread_count": row[0] if row else 0}


async def create_notification(
    notification: dict, database_path: str | Path | None = None
) -> dict:
    """Create one notification using the existing API response contract."""
    async with connect_to_database(database_path) as db:
        await db.execute(
            """
            INSERT INTO notifications (user_id, trip_id, title, body, type, link)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                notification["user_id"],
                notification["trip_id"],
                notification["title"],
                notification["body"],
                notification["type"],
                notification["link"],
            ),
        )
        await db.commit()

    return {"message": "Notification created"}


async def broadcast_notification(
    title: str,
    body: str,
    trip_id: str = "ross26",
    type: str = "info",
    link: str | None = None,
    database_path: str | Path | None = None,
) -> dict:
    """Create the same notification for every user currently in the trip."""
    async with connect_to_database(database_path) as db:
        cursor = await db.execute("SELECT id FROM users")
        users = await cursor.fetchall()
        for user_row in users:
            await db.execute(
                """
                INSERT INTO notifications (user_id, trip_id, title, body, type, link)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_row[0], trip_id, title, body, type, link),
            )
        await db.commit()

    return {"message": f"Notification sent to {len(users)} users"}


async def mark_notification_read(
    notification_id: int, database_path: str | Path | None = None
) -> dict:
    """Mark one notification as read."""
    async with connect_to_database(database_path) as db:
        await db.execute(
            "UPDATE notifications SET read = TRUE WHERE id = ?",
            (notification_id,),
        )
        await db.commit()

    return {"message": "Notification marked as read"}


async def mark_all_read(
    user_id: int, database_path: str | Path | None = None
) -> dict:
    """Mark all notifications as read for one user."""
    async with connect_to_database(database_path) as db:
        await db.execute(
            "UPDATE notifications SET read = TRUE WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()

    return {"message": "All notifications marked as read"}

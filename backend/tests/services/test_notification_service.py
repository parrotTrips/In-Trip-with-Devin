import asyncio
import sqlite3

from app.db.database import init_db
from app.services.notification_service import (
    broadcast_notification,
    create_notification,
    get_notifications,
    get_unread_count,
    mark_all_read,
    mark_notification_read,
)


def seed_user(database_path, phone, name=None):
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO users (phone, name) VALUES (?, ?)",
            (phone, name),
        )
        connection.commit()
        return cursor.lastrowid


def test_notification_service_reads_and_marks_notifications(tmp_path):
    database_path = tmp_path / "notifications.db"
    asyncio.run(init_db(database_path))
    user_id = seed_user(database_path, "+5511880000000")

    create_response = asyncio.run(
        create_notification(
            {
                "user_id": user_id,
                "trip_id": "ross26",
                "title": "Heads up",
                "body": "Trip update",
                "type": "info",
                "link": "/profile",
            },
            database_path=database_path,
        )
    )
    notifications_response = asyncio.run(
        get_notifications(user_id, database_path=database_path)
    )
    unread_response = asyncio.run(get_unread_count(user_id, database_path=database_path))
    mark_response = asyncio.run(
        mark_notification_read(
            notifications_response["notifications"][0]["id"],
            database_path=database_path,
        )
    )
    read_all_response = asyncio.run(mark_all_read(user_id, database_path=database_path))
    final_unread_response = asyncio.run(
        get_unread_count(user_id, database_path=database_path)
    )

    assert create_response == {"message": "Notification created"}
    assert notifications_response["unread_count"] == 1
    assert notifications_response["notifications"][0]["title"] == "Heads up"
    assert notifications_response["notifications"][0]["read"] is False
    assert unread_response == {"unread_count": 1}
    assert mark_response == {"message": "Notification marked as read"}
    assert read_all_response == {"message": "All notifications marked as read"}
    assert final_unread_response == {"unread_count": 0}


def test_notification_service_broadcasts_to_all_users(tmp_path):
    database_path = tmp_path / "notifications.db"
    asyncio.run(init_db(database_path))
    seed_user(database_path, "+5511880000001")
    seed_user(database_path, "+5511880000002")

    response = asyncio.run(
        broadcast_notification(
            title="Broadcast",
            body="All travelers",
            database_path=database_path,
        )
    )

    assert response == {"message": "Notification sent to 2 users"}

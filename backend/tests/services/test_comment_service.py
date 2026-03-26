import asyncio
import sqlite3

from app.db.database import init_db
from app.services.comment_service import add_comment, get_comments


def seed_user(database_path, phone, name=None):
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO users (phone, name) VALUES (?, ?)",
            (phone, name),
        )
        connection.commit()
        return cursor.lastrowid


def test_get_comments_returns_only_public_comments(tmp_path):
    database_path = tmp_path / "comments.db"
    asyncio.run(init_db(database_path))
    user_id = seed_user(database_path, "+5511000000001", "Dana")

    asyncio.run(
        add_comment(
            user_id,
            {
                "trip_id": "ross26",
                "phase_id": "phase-1",
                "text": "Public comment",
                "is_private": False,
            },
            database_path=database_path,
        )
    )
    asyncio.run(
        add_comment(
            user_id,
            {
                "trip_id": "ross26",
                "phase_id": "phase-1",
                "text": "Private comment",
                "is_private": True,
            },
            database_path=database_path,
        )
    )

    response = asyncio.run(
        get_comments("ross26", "phase-1", database_path=database_path)
    )

    assert response["trip_id"] == "ross26"
    assert response["phase_id"] == "phase-1"
    assert len(response["comments"]) == 1
    assert response["comments"][0]["user_name"] == "Dana"
    assert response["comments"][0]["text"] == "Public comment"
    assert response["comments"][0]["is_private"] is False

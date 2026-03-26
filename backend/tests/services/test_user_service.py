import asyncio
import sqlite3

from app.db.database import init_db
from app.services.user_service import get_user, update_user


def seed_user(database_path, phone="+5511777777777", name=None):
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO users (phone, name) VALUES (?, ?)",
            (phone, name),
        )
        connection.commit()
        return cursor.lastrowid


def test_get_user_returns_user_data(tmp_path):
    database_path = tmp_path / "users.db"
    asyncio.run(init_db(database_path))
    user_id = seed_user(database_path, name="Alice")

    response = asyncio.run(get_user(user_id, database_path=database_path))

    assert response == {
        "id": user_id,
        "phone": "+5511777777777",
        "name": "Alice",
    }


def test_update_user_persists_name_changes(tmp_path):
    database_path = tmp_path / "users.db"
    asyncio.run(init_db(database_path))
    user_id = seed_user(database_path)

    response = asyncio.run(
        update_user(user_id, {"name": "Bob"}, database_path=database_path)
    )
    updated_user = asyncio.run(get_user(user_id, database_path=database_path))

    assert response == {"message": "User updated"}
    assert updated_user == {
        "id": user_id,
        "phone": "+5511777777777",
        "name": "Bob",
    }

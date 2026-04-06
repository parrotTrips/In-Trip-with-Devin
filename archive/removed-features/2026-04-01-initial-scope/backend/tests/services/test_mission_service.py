import asyncio
import sqlite3

from app.db.database import init_db
from app.services.mission_service import (
    complete_mission,
    create_mission,
    get_leaderboard,
    get_missions,
    get_user_points,
    uncomplete_mission,
)


def seed_user(database_path, phone, name=None):
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO users (phone, name) VALUES (?, ?)",
            (phone, name),
        )
        connection.commit()
        return cursor.lastrowid


def test_mission_service_reads_and_toggles_completion(tmp_path):
    database_path = tmp_path / "missions.db"
    asyncio.run(init_db(database_path))
    user_id = seed_user(database_path, "+5511770000000")

    missions_response = asyncio.run(
        get_missions("ross26", user_id=user_id, database_path=database_path)
    )
    mission_id = missions_response["missions"][0]["id"]
    complete_response = asyncio.run(
        complete_mission("ross26", user_id, mission_id, database_path=database_path)
    )
    completed_missions_response = asyncio.run(
        get_missions("ross26", user_id=user_id, database_path=database_path)
    )
    uncomplete_response = asyncio.run(
        uncomplete_mission("ross26", user_id, mission_id, database_path=database_path)
    )

    assert missions_response["trip_id"] == "ross26"
    assert len(missions_response["missions"]) == 12
    assert complete_response["message"] == "Mission completed!"
    assert complete_response["already_completed"] is False
    assert completed_missions_response["missions"][0]["completed"] is True
    assert uncomplete_response == {"message": "Mission uncompleted"}


def test_mission_service_reports_leaderboard_and_points(tmp_path):
    database_path = tmp_path / "missions.db"
    asyncio.run(init_db(database_path))
    alice_id = seed_user(database_path, "+5511770000001", "Alice")
    bob_id = seed_user(database_path, "+5511770000002", "Bob")
    asyncio.run(
        create_mission(
            {
                "trip_id": "ross26",
                "title": "Bonus",
                "description": "Worth extra points",
                "points": 500,
                "icon": "⭐",
                "category": "bonus",
                "sort_order": 99,
            },
            database_path=database_path,
        )
    )
    missions_response = asyncio.run(get_missions("ross26", database_path=database_path))
    bonus_mission = next(
        mission for mission in missions_response["missions"] if mission["title"] == "Bonus"
    )
    asyncio.run(
        complete_mission("ross26", alice_id, bonus_mission["id"], database_path=database_path)
    )

    leaderboard_response = asyncio.run(
        get_leaderboard("ross26", database_path=database_path)
    )
    points_response = asyncio.run(
        get_user_points("ross26", alice_id, database_path=database_path)
    )
    bob_points_response = asyncio.run(
        get_user_points("ross26", bob_id, database_path=database_path)
    )

    assert leaderboard_response["trip_id"] == "ross26"
    assert leaderboard_response["leaderboard"][0]["user_id"] == alice_id
    assert leaderboard_response["leaderboard"][0]["total_points"] == 500
    assert points_response == {
        "user_id": alice_id,
        "total_points": 500,
        "missions_completed": 1,
    }
    assert bob_points_response == {
        "user_id": bob_id,
        "total_points": 0,
        "missions_completed": 0,
    }

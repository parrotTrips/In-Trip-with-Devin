import asyncio

from app.db.database import init_db
from app.services.checklist_service import (
    get_checklist_progress,
    get_phase_completions,
    update_checklist_item,
    update_phase_completion,
)


def test_checklist_progress_is_persisted_per_phase_and_item(tmp_path):
    database_path = tmp_path / "checklist.db"
    asyncio.run(init_db(database_path))

    asyncio.run(
        update_checklist_item(
            7,
            {
                "trip_id": "ross26",
                "phase_id": "phase-1",
                "item_id": "passport",
                "completed": True,
            },
            database_path=database_path,
        )
    )
    asyncio.run(
        update_checklist_item(
            7,
            {
                "trip_id": "ross26",
                "phase_id": "phase-1",
                "item_id": "insurance",
                "completed": False,
            },
            database_path=database_path,
        )
    )

    response = asyncio.run(
        get_checklist_progress("ross26", 7, database_path=database_path)
    )

    assert response == {
        "trip_id": "ross26",
        "user_id": 7,
        "progress": {
            "phase-1": {
                "passport": True,
                "insurance": False,
            }
        },
    }


def test_phase_completion_is_persisted_per_user_and_phase(tmp_path):
    database_path = tmp_path / "checklist.db"
    asyncio.run(init_db(database_path))

    update_response = asyncio.run(
        update_phase_completion(
            7,
            {"trip_id": "ross26", "phase_id": "phase-1", "completed": True},
            database_path=database_path,
        )
    )
    completions_response = asyncio.run(
        get_phase_completions("ross26", 7, database_path=database_path)
    )

    assert update_response == {"message": "Phase completion updated"}
    assert completions_response == {
        "trip_id": "ross26",
        "user_id": 7,
        "completions": {"phase-1": True},
    }

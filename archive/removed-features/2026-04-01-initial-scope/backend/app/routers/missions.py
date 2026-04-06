"""Mission HTTP routes."""

from typing import Optional

from fastapi import APIRouter

from app.schemas.missions import MissionComplete, MissionCreate
from app.services.mission_service import (
    complete_mission,
    create_mission,
    get_leaderboard,
    get_missions,
    get_user_points,
    uncomplete_mission,
)

router = APIRouter(tags=["missions"])


@router.get("/missions/{trip_id}")
async def get_missions_handler(trip_id: str, user_id: Optional[int] = None):
    """Return active missions for one trip."""
    return await get_missions(trip_id, user_id=user_id)


@router.post("/missions/{trip_id}/complete")
async def complete_mission_handler(trip_id: str, user_id: int, body: MissionComplete):
    """Persist one mission completion."""
    return await complete_mission(trip_id, user_id, body.mission_id)


@router.delete("/missions/{trip_id}/uncomplete")
async def uncomplete_mission_handler(
    trip_id: str, user_id: int, body: MissionComplete
):
    """Undo one mission completion."""
    return await uncomplete_mission(trip_id, user_id, body.mission_id)


@router.get("/missions/{trip_id}/leaderboard")
async def get_leaderboard_handler(trip_id: str):
    """Return the mission leaderboard for one trip."""
    return await get_leaderboard(trip_id)


@router.get("/missions/{trip_id}/user/{user_id}/points")
async def get_user_points_handler(trip_id: str, user_id: int):
    """Return points and completion count for one user."""
    return await get_user_points(trip_id, user_id)


@router.post("/missions")
async def create_mission_handler(mission: MissionCreate):
    """Create one mission through the admin endpoint."""
    return await create_mission(mission.model_dump())

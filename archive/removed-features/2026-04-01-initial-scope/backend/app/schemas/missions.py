"""Mission schemas."""

from pydantic import BaseModel


class MissionCreate(BaseModel):
    """Payload used by the admin endpoint that creates a mission."""

    trip_id: str = "ross26"
    title: str
    description: str
    points: int = 50
    icon: str = "🎯"
    category: str = "general"
    sort_order: int = 0


class MissionComplete(BaseModel):
    """Mission identifier used to complete or undo a mission."""

    mission_id: int

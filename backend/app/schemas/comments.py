"""Comment schemas."""

from pydantic import BaseModel


class CommentCreate(BaseModel):
    """Fields required to add a phase comment."""

    trip_id: str
    phase_id: str
    text: str
    is_private: bool = False

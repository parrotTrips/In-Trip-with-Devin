"""Comment HTTP routes."""

from fastapi import APIRouter

from app.schemas.comments import CommentCreate
from app.services.comment_service import add_comment, get_comments

router = APIRouter(tags=["comments"])


@router.post("/comments")
async def add_comment_handler(user_id: int, comment: CommentCreate):
    """Persist one comment for a trip phase."""
    return await add_comment(user_id, comment.model_dump())


@router.get("/comments/{trip_id}/{phase_id}")
async def get_comments_handler(trip_id: str, phase_id: str):
    """Return public comments for a trip phase."""
    return await get_comments(trip_id, phase_id)

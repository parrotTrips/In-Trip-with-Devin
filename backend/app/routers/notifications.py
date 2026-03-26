"""Notification HTTP routes."""

from typing import Optional

from fastapi import APIRouter

from app.schemas.notifications import NotificationCreate
from app.services.notification_service import (
    broadcast_notification,
    create_notification,
    get_notifications,
    get_unread_count,
    mark_all_read,
    mark_notification_read,
)

router = APIRouter(tags=["notifications"])


@router.get("/notifications/{user_id}")
async def get_notifications_handler(user_id: int, unread_only: bool = False):
    """Return notifications for one user."""
    return await get_notifications(user_id, unread_only=unread_only)


@router.get("/notifications/{user_id}/count")
async def get_unread_count_handler(user_id: int):
    """Return only the unread notification count."""
    return await get_unread_count(user_id)


@router.post("/notifications")
async def create_notification_handler(notification: NotificationCreate):
    """Create one notification."""
    return await create_notification(notification.model_dump())


@router.post("/notifications/broadcast")
async def broadcast_notification_handler(
    title: str,
    body: str,
    trip_id: str = "ross26",
    type: str = "info",
    link: Optional[str] = None,
):
    """Broadcast one notification to all users."""
    return await broadcast_notification(
        title=title,
        body=body,
        trip_id=trip_id,
        type=type,
        link=link,
    )


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read_handler(notification_id: int):
    """Mark one notification as read."""
    return await mark_notification_read(notification_id)


@router.put("/notifications/{user_id}/read-all")
async def mark_all_read_handler(user_id: int):
    """Mark all notifications as read for one user."""
    return await mark_all_read(user_id)

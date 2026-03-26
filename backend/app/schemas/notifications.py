"""Notification schemas."""

from typing import Optional

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    """Payload used to create a notification for one traveler."""

    user_id: int
    trip_id: str = "ross26"
    title: str
    body: str
    type: str = "info"
    link: Optional[str] = None

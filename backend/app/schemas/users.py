"""User-related schemas."""

from typing import Optional

from pydantic import BaseModel


class UserUpdate(BaseModel):
    """Fields accepted when updating a user."""

    name: Optional[str] = None

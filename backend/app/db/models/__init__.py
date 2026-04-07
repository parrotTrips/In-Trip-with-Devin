"""Import all SQLAlchemy models so metadata is fully populated."""

from app.db.models.auth import OTPCode
from app.db.models.media import ActivityMedia, MediaAsset
from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.traveler import TravelerProduct, TravelerProfile
from app.db.models.trip import (
    Trip,
    TripActivity,
    TripPhase,
    TripPhaseChecklistItem,
    TripPhaseLink,
    TripTraveler,
)
from app.db.models.user import User

__all__ = [
    "ActivityMedia",
    "MediaAsset",
    "OTPCode",
    "TravelerChecklistProgress",
    "TravelerPhaseProgress",
    "TravelerProduct",
    "TravelerProfile",
    "Trip",
    "TripActivity",
    "TripPhase",
    "TripPhaseChecklistItem",
    "TripPhaseLink",
    "TripTraveler",
    "User",
]

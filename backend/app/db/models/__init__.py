"""Import all SQLAlchemy models so metadata is fully populated."""

from app.db.models.auth import OTPCode
from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.staff import StaffTask, TripContact, TripStaff
from app.db.models.traveler import TravelerProfile
from app.db.models.trip import (
    TripActivity,
    TripPhase,
    TripPhaseChecklistItem,
    TripPhaseLink,
    TripTraveler,
)
from app.db.models.user import User

__all__ = [
    "OTPCode",
    "StaffTask",
    "TravelerChecklistProgress",
    "TravelerPhaseProgress",
    "TravelerProfile",
    "TripActivity",
    "TripPhase",
    "TripPhaseChecklistItem",
    "TripPhaseLink",
    "TripContact",
    "TripStaff",
    "TripTraveler",
    "User",
]

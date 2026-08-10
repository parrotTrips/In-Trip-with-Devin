"""Import all SQLAlchemy models so metadata is fully populated."""

from app.db.models.auth import OTPCode
from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.staff import (
    ActivityCheckin,
    ActivityCheckinScanEvent,
    ActivityParticipant,
    StaffTask,
    TripAnnouncement,
    TripContact,
    TripStaff,
)
from app.db.models.traveler import TravelerProfile
from app.db.models.trip import (
    TripActivity,
    TripCancellationPolicy,
    TripEmergencyContact,
    TripFaq,
    TripPhase,
    TripPhaseChecklistItem,
    TripPhaseLink,
    TripRecommendation,
    TripTraveler,
)
from app.db.models.user import User

__all__ = [
    "OTPCode",
    "ActivityCheckin",
    "ActivityCheckinScanEvent",
    "ActivityParticipant",
    "StaffTask",
    "TravelerChecklistProgress",
    "TravelerPhaseProgress",
    "TravelerProfile",
    "TripActivity",
    "TripCancellationPolicy",
    "TripEmergencyContact",
    "TripFaq",
    "TripPhase",
    "TripPhaseChecklistItem",
    "TripPhaseLink",
    "TripRecommendation",
    "TripAnnouncement",
    "TripContact",
    "TripStaff",
    "TripTraveler",
    "User",
]

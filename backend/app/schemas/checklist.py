"""Checklist and phase completion schemas."""

from pydantic import BaseModel


class ChecklistUpdate(BaseModel):
    """Payload used to persist one checklist item state."""

    trip_id: str
    phase_id: str
    item_id: str
    completed: bool


class PhaseCompletionUpdate(BaseModel):
    """Payload used to persist a phase completion state."""

    trip_id: str
    phase_id: str
    completed: bool

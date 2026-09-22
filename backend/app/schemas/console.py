"""Pydantic contracts for the console API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PhaseCreate(BaseModel):
    title: str
    subtitle: str | None = None
    icon: str | None = None
    short_description: str = ""
    detailed_description: str | None = None


class PhaseUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    icon: str | None = None
    short_description: str | None = None
    detailed_description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ChecklistItemIn(BaseModel):
    label: str
    is_required: bool = False


class ChecklistReplace(BaseModel):
    items: list[ChecklistItemIn] = []


class LinkIn(BaseModel):
    label: str
    url: str


class LinkReplace(BaseModel):
    links: list[LinkIn] = []


class PhaseOrder(BaseModel):
    phase_ids: list[str] = []


class SectionReplace(BaseModel):
    """Rows of an editable section. Keys are filtered against the section registry."""

    items: list[dict] = Field(default_factory=list)


class ActivityIn(BaseModel):
    """Fields of an activity. Unknown keys are ignored by the service."""

    name: str | None = None
    activity_type: str | None = None
    starts_at: datetime | None = None
    duration_minutes: int | None = None
    short_description: str | None = None
    practical_info: str | None = None
    address: str | None = None
    max_checkins: int | None = None
    amount_brl: float | None = None


class ActivityOrder(BaseModel):
    activity_ids: list[str] = Field(default_factory=list)

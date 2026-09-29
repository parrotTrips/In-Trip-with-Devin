"""Pydantic contracts for the console API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class _NonBlankModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def strip_required_strings(cls, value, info):
        if info.field_name in {"title", "short_description", "label"} and isinstance(value, str):
            return value.strip()
        return value


class PhaseCreate(_NonBlankModel):
    title: str = Field(min_length=1)
    subtitle: str | None = None
    icon: str | None = None
    short_description: str = Field(min_length=1)
    detailed_description: str | None = None


class PhaseUpdate(_NonBlankModel):
    title: str | None = Field(default=None, min_length=1)
    subtitle: str | None = None
    icon: str | None = None
    short_description: str | None = Field(default=None, min_length=1)
    detailed_description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ChecklistItemIn(_NonBlankModel):
    label: str = Field(min_length=1)
    is_required: bool = False


class ChecklistReplace(BaseModel):
    items: list[ChecklistItemIn] = Field(default_factory=list)


class LinkIn(_NonBlankModel):
    label: str = Field(min_length=1)
    url: HttpUrl


class LinkReplace(BaseModel):
    links: list[LinkIn] = Field(default_factory=list)


class PhaseOrder(BaseModel):
    phase_ids: list[str] = Field(default_factory=list)


class PhaseContentUpdate(_NonBlankModel):
    title: str = Field(min_length=1)
    subtitle: str | None = None
    icon: str | None = None
    short_description: str = Field(min_length=1)
    detailed_description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    checklist: list[ChecklistItemIn] = Field(default_factory=list)
    links: list[LinkIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def dates_are_ordered(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("ends_at must not be earlier than starts_at")
        return self


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


class DayCreate(_NonBlankModel):
    title: str = Field(min_length=1)
    short_description: str = ""

"""Pydantic contracts for the console API."""

from __future__ import annotations

from pydantic import BaseModel


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

"""
Read a filled Google Sheets spreadsheet for a single trip and upsert its
content into Supabase (trip_phases, checklist_items, links, activities).

Usage:
  cd backend
  poetry run python scripts/import_trip_content.py --sheet-id <SPREADSHEET_ID>

The SPREADSHEET_ID is the long ID in the sheet URL:
  https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit

Prerequisites:
  - secrets/gcp-oauth2-credentials.json  (OAuth2 Desktop app client)
  - secrets/gcp-oauth2-token.json        (auto-created on first run)
  - DATABASE_URL in backend/.env
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

_TOKEN_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-token.json"
_OAUTH2_CREDS_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-credentials.json"

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/parrot_trips",
)
PG_URL = (
    DATABASE_URL
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("postgresql+psycopg2://", "postgresql://")
)


def _get_credentials() -> Credentials:
    creds: Credentials | None = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not _OAUTH2_CREDS_FILE.exists():
                print(f"ERROR: OAuth2 credentials file not found: {_OAUTH2_CREDS_FILE}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(_OAUTH2_CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_FILE.write_text(creds.to_json())
    return creds


def build_sheets_client():
    return build("sheets", "v4", credentials=_get_credentials())


def read_tab(sheets_svc, sheet_id: str, tab_name: str) -> list[list[str]]:
    """Return all rows of a tab as list-of-lists (strings). Empty cells become ''."""
    resp = (
        sheets_svc.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=tab_name)
        .execute()
    )
    return resp.get("values", [])


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class TripConfig:
    trip_uuid: str
    trip_title: str
    start_date: str  # YYYY-MM-DD string — used to compute starts_at for days


@dataclass
class ChecklistItem:
    label: str
    is_required: bool
    sort_order: int


@dataclass
class PhaseLink:
    label: str
    url: str
    sort_order: int


@dataclass
class PreTripPhase:
    fase: str           # visa | vaccination | packing | documents
    title: str
    subtitle: str
    icon: str
    short_description: str
    detailed_description: str
    checklist: list[ChecklistItem] = field(default_factory=list)
    links: list[PhaseLink] = field(default_factory=list)


@dataclass
class Activity:
    name: str
    activity_type: str   # included | optional | suggested | logistics
    horario: str         # raw string e.g. "10:00" — stored in short_description context
    duration_minutes: int | None
    short_description: str
    practical_info: str
    amount_brl: float | None
    sort_order: int


@dataclass
class InTripDay:
    dia: int             # day number (1-based)
    data: str            # YYYY-MM-DD
    title: str
    subtitle: str
    icon: str
    short_description: str
    detailed_description: str
    activities: list[Activity] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_config_tab(rows: list[list[str]]) -> TripConfig:
    """Parse Config tab rows into TripConfig. First row is header."""
    data: dict[str, str] = {}
    for row in rows[1:]:  # skip header
        if len(row) >= 2:
            data[row[0].strip()] = row[1].strip()
    if not data.get("trip_uuid"):
        raise ValueError("Config tab is missing required key: trip_uuid")
    return TripConfig(
        trip_uuid=data["trip_uuid"],
        trip_title=data.get("trip_title", ""),
        start_date=data.get("start_date", ""),
    )


def parse_pre_trip_tab(rows: list[list[str]]) -> list[PreTripPhase]:
    """Parse Pre-Trip tab. Returns one PreTripPhase per distinct fase value."""
    phases: dict[str, PreTripPhase] = {}
    checklist_by_fase: dict[str, dict[int, dict[str, str]]] = {}
    links_by_fase: dict[str, dict[int, dict[str, str]]] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 5:
            continue
        fase, bloco, ordem_str, campo, valor = (row[i].strip() if i < len(row) else "" for i in range(5))
        if not fase or not bloco or not campo:
            continue

        try:
            ordem = int(ordem_str)
        except ValueError:
            continue

        if bloco == "header":
            if fase not in phases:
                phases[fase] = PreTripPhase(
                    fase=fase, title="", subtitle="", icon="",
                    short_description="", detailed_description="",
                )
            p = phases[fase]
            if campo == "title":
                p.title = valor
            elif campo == "subtitle":
                p.subtitle = valor
            elif campo == "icon":
                p.icon = valor
            elif campo == "short_description":
                p.short_description = valor
            elif campo == "detailed_description":
                p.detailed_description = valor

        elif bloco == "checklist":
            if fase not in checklist_by_fase:
                checklist_by_fase[fase] = {}
            if ordem not in checklist_by_fase[fase]:
                checklist_by_fase[fase][ordem] = {}
            checklist_by_fase[fase][ordem][campo] = valor

        elif bloco == "link":
            if fase not in links_by_fase:
                links_by_fase[fase] = {}
            if ordem not in links_by_fase[fase]:
                links_by_fase[fase][ordem] = {}
            links_by_fase[fase][ordem][campo] = valor

    # Assemble checklist and links into phases
    for fase, phase in phases.items():
        for sort_order, fields in sorted(checklist_by_fase.get(fase, {}).items()):
            label = fields.get("label", "")
            if not label:
                continue
            is_required = fields.get("is_required", "false").lower() == "true"
            phase.checklist.append(ChecklistItem(label=label, is_required=is_required, sort_order=sort_order - 1))

        for sort_order, fields in sorted(links_by_fase.get(fase, {}).items()):
            label = fields.get("label", "")
            url = fields.get("url", "")
            if not label or not url:
                continue
            phase.links.append(PhaseLink(label=label, url=url, sort_order=sort_order - 1))

    return list(phases.values())


def parse_roteiro_tab(rows: list[list[str]]) -> list[InTripDay]:
    """Parse Roteiro (itinerary) tab rows into list of InTripDay. Implementation in Task 4."""
    # TODO: Task 4 implementation
    raise NotImplementedError("parse_roteiro_tab to be implemented in Task 4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import trip content from a Google Sheets spreadsheet into Supabase"
    )
    parser.add_argument(
        "--sheet-id",
        required=True,
        help="Google Sheets spreadsheet ID (from the URL: /spreadsheets/d/<ID>/edit)",
    )
    args = parser.parse_args()
    print(f"Sheet ID: {args.sheet_id} (implementation coming in later tasks)")

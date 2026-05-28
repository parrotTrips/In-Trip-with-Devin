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


_ROTEIRO_COLS = [
    "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon",
    "dia_descricao_curta", "dia_descricao_completa",
    "atividade_nome", "atividade_tipo", "atividade_horario",
    "atividade_duracao_min", "atividade_descricao_curta",
    "atividade_info_pratica", "atividade_preco_brl",
]


def _cell(row: list[str], col: str) -> str:
    try:
        idx = _ROTEIRO_COLS.index(col)
        return row[idx].strip() if idx < len(row) else ""
    except ValueError:
        return ""


def parse_roteiro_tab(rows: list[list[str]]) -> list[InTripDay]:
    """Parse Roteiro tab. Returns one InTripDay per distinct dia value, preserving order."""
    days: dict[int, InTripDay] = {}
    activity_counters: dict[int, int] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 8:
            continue
        dia_str = _cell(row, "dia")
        if not dia_str.isdigit():
            continue
        dia = int(dia_str)

        if dia not in days:
            days[dia] = InTripDay(
                dia=dia,
                data=_cell(row, "data"),
                title=_cell(row, "dia_titulo"),
                subtitle=_cell(row, "dia_subtitulo"),
                icon=_cell(row, "dia_icon"),
                short_description=_cell(row, "dia_descricao_curta"),
                detailed_description=_cell(row, "dia_descricao_completa"),
            )
            activity_counters[dia] = 0

        atividade_nome = _cell(row, "atividade_nome")
        if not atividade_nome:
            continue

        dur_str = _cell(row, "atividade_duracao_min")
        duration_minutes: int | None = int(dur_str) if dur_str.isdigit() else None

        preco_str = _cell(row, "atividade_preco_brl")
        amount_brl: float | None = None
        try:
            if preco_str:
                amount_brl = float(preco_str)
        except ValueError:
            pass

        days[dia].activities.append(Activity(
            name=atividade_nome,
            activity_type=_cell(row, "atividade_tipo"),
            horario=_cell(row, "atividade_horario"),
            duration_minutes=duration_minutes,
            short_description=_cell(row, "atividade_descricao_curta"),
            practical_info=_cell(row, "atividade_info_pratica"),
            amount_brl=amount_brl,
            sort_order=activity_counters[dia],
        ))
        activity_counters[dia] += 1

    return list(days.values())


async def write_to_db(
    conn: asyncpg.Connection,
    config: TripConfig,
    pre_trip_phases: list[PreTripPhase],
    in_trip_days: list[InTripDay],
) -> None:
    """Delete all existing phase data for the trip and insert fresh rows. Runs in a transaction."""
    trip_uuid = config.trip_uuid

    async with conn.transaction():
        # 1. Delete traveler progress that references checklist items and phases for this trip
        phase_ids = await conn.fetch(
            "SELECT id FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if phase_ids:
            ids = [str(r["id"]) for r in phase_ids]
            traveler_rows = await conn.fetch(
                "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
            )
            if traveler_rows:
                tt_ids = [str(r["id"]) for r in traveler_rows]
                await conn.execute(
                    "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
                await conn.execute(
                    "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
            await conn.execute(
                "DELETE FROM trip_activities WHERE trip_phase_id = ANY($1::uuid[])", ids
            )
            await conn.execute(
                "DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = ANY($1::uuid[])", ids
            )
            await conn.execute(
                "DELETE FROM trip_phase_links WHERE trip_phase_id = ANY($1::uuid[])", ids
            )
            await conn.execute(
                "DELETE FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
            )

        # 2. Insert pre-trip phases
        FIXED_PHASE_ORDER = ["visa", "vaccination", "packing", "documents"]
        phase_map = {p.fase: p for p in pre_trip_phases}
        sort_order = 0
        for fase_key in FIXED_PHASE_ORDER:
            phase = phase_map.get(fase_key)
            if not phase:
                continue
            phase_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO trip_phases
                    (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                     short_description, detailed_description, sort_order,
                     is_locked_by_default, is_visible, created_at, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,now(),now())
                """,
                phase_id, trip_uuid, "pre-trip", phase.title, phase.subtitle,
                phase.icon, phase.short_description, phase.detailed_description,
                sort_order, False, True,
            )
            sort_order += 1
            for item in phase.checklist:
                await conn.execute(
                    """
                    INSERT INTO trip_phase_checklist_items
                        (id, trip_phase_id, label, sort_order, is_required, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,now(),now())
                    """,
                    str(uuid.uuid4()), phase_id, item.label, item.sort_order, item.is_required,
                )
            for link in phase.links:
                await conn.execute(
                    """
                    INSERT INTO trip_phase_links
                        (id, trip_phase_id, label, url, sort_order, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,now(),now())
                    """,
                    str(uuid.uuid4()), phase_id, link.label, link.url, link.sort_order,
                )

        # 3. Insert in-trip days
        for day in in_trip_days:
            phase_id = str(uuid.uuid4())
            try:
                starts_at = datetime.strptime(day.data, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                starts_at = None
            await conn.execute(
                """
                INSERT INTO trip_phases
                    (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                     short_description, detailed_description, sort_order,
                     starts_at, is_locked_by_default, is_visible, created_at, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,now(),now())
                """,
                phase_id, trip_uuid, "in-trip", day.title, day.subtitle,
                day.icon, day.short_description, day.detailed_description,
                sort_order, starts_at, False, True,
            )
            sort_order += 1
            for act in day.activities:
                await conn.execute(
                    """
                    INSERT INTO trip_activities
                        (id, trip_phase_id, name, activity_type,
                         duration_minutes, short_description, practical_info,
                         amount_brl, sort_order, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,now(),now())
                    """,
                    str(uuid.uuid4()), phase_id, act.name, act.activity_type,
                    act.duration_minutes, act.short_description,
                    act.practical_info or None, act.amount_brl, act.sort_order,
                )


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

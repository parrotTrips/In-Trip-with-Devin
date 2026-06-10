"""
Read a filled Google Sheets spreadsheet (single sheet for all trips) and upsert
content for a specific trip into Supabase (trip_phases, checklist_items, links, activities).

Usage:
  cd backend
  poetry run python scripts/import_trip_content.py --trip-uuid gsb-nye-2026

The spreadsheet ID is read from TRIP_CONTENT_SHEET_ID in backend/.env.

Prerequisites:
  - secrets/gcp-oauth2-credentials.json  (OAuth2 Desktop app client)
  - secrets/gcp-oauth2-token.json        (auto-created on first run)
  - DATABASE_URL in backend/.env
  - TRIP_CONTENT_SHEET_ID in backend/.env
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

TRIP_CONTENT_SHEET_ID = os.environ.get("TRIP_CONTENT_SHEET_ID", "")


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


def parse_service_agreement_url(viagens_rows: list[list[str]], trip_uuid: str) -> str | None:
    """Read service_agreement_url for a trip from the Viagens tab.
    Expected columns: trip_uuid, nome_da_viagem, data_inicio, data_fim, service_agreement_url
    """
    if not viagens_rows or len(viagens_rows) < 2:
        return None
    header = [h.strip().lower() for h in viagens_rows[0]]
    try:
        uuid_col = header.index("trip_uuid")
        url_col = header.index("service_agreement_url")
    except ValueError:
        return None
    for row in viagens_rows[1:]:
        if len(row) > uuid_col and row[uuid_col].strip() == trip_uuid:
            url = row[url_col].strip() if len(row) > url_col else ""
            return url or None
    return None


def filter_rows_by_trip(rows: list[list[str]], trip_uuid: str) -> list[list[str]]:
    """Keep header row and data rows whose first column matches trip_uuid."""
    if not rows:
        return []
    header = rows[0]
    matching = [row for row in rows[1:] if row and row[0].strip() == trip_uuid]
    return [header] + matching


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

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
    fase: str
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
    activity_type: str
    horario: str
    duration_minutes: int | None
    short_description: str
    practical_info: str
    amount_brl: float | None
    sort_order: int


@dataclass
class InTripDay:
    dia: int
    data: str
    title: str
    subtitle: str
    icon: str
    short_description: str
    detailed_description: str
    activities: list[Activity] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_fases_tab(rows: list[list[str]]) -> list[PreTripPhase]:
    """Parse Fases tab (already filtered by trip_uuid). Each row is one complete phase.
    Columns: trip_uuid, ordem, fase, titulo, subtitulo, icone, descricao_curta, descricao_completa
    Returns phases sorted by ordem."""
    phases: list[tuple[int, PreTripPhase]] = []
    for row in rows[1:]:  # skip header
        if len(row) < 8:
            continue
        _, ordem_str, fase, titulo, subtitulo, icone, descricao_curta, descricao_completa = (
            row[i].strip() if i < len(row) else "" for i in range(8)
        )
        if not fase:
            continue
        try:
            ordem = int(ordem_str)
        except ValueError:
            continue
        phases.append((ordem, PreTripPhase(
            fase=fase,
            title=titulo,
            subtitle=subtitulo,
            icon=icone,
            short_description=descricao_curta,
            detailed_description=descricao_completa,
        )))
    return [p for _, p in sorted(phases, key=lambda x: x[0])]


def parse_checklist_tab(rows: list[list[str]], phases: list[PreTripPhase]) -> None:
    """Parse Checklist tab (already filtered by trip_uuid) and attach items to phases in-place.
    Columns: trip_uuid, fase, ordem, label, obrigatorio"""
    phase_map = {p.fase: p for p in phases}
    by_fase: dict[str, dict[int, dict[str, str]]] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 5:
            continue
        _, fase, ordem_str, label, obrigatorio = (
            row[i].strip() if i < len(row) else "" for i in range(5)
        )
        if not fase or not label:
            continue
        try:
            ordem = int(ordem_str)
        except ValueError:
            continue
        if fase not in by_fase:
            by_fase[fase] = {}
        by_fase[fase][ordem] = {"label": label, "obrigatorio": obrigatorio}

    for fase, items in by_fase.items():
        phase = phase_map.get(fase)
        if not phase:
            continue
        for sort_order, fields in sorted(items.items()):
            is_required = fields["obrigatorio"].lower() == "true"
            phase.checklist.append(ChecklistItem(
                label=fields["label"],
                is_required=is_required,
                sort_order=sort_order - 1,
            ))


def parse_links_tab(rows: list[list[str]], phases: list[PreTripPhase]) -> None:
    """Parse Links tab (already filtered by trip_uuid) and attach links to phases in-place.
    Columns: trip_uuid, fase, ordem, label, url"""
    phase_map = {p.fase: p for p in phases}
    by_fase: dict[str, dict[int, dict[str, str]]] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 5:
            continue
        _, fase, ordem_str, label, url = (
            row[i].strip() if i < len(row) else "" for i in range(5)
        )
        if not fase or not label or not url:
            continue
        try:
            ordem = int(ordem_str)
        except ValueError:
            continue
        if fase not in by_fase:
            by_fase[fase] = {}
        by_fase[fase][ordem] = {"label": label, "url": url}

    for fase, links in by_fase.items():
        phase = phase_map.get(fase)
        if not phase:
            continue
        for sort_order, fields in sorted(links.items()):
            phase.links.append(PhaseLink(
                label=fields["label"],
                url=fields["url"],
                sort_order=sort_order - 1,
            ))


_ROTEIRO_COLS = [
    "trip_uuid",
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
    """Parse Roteiro tab rows (already filtered by trip_uuid)."""
    days: dict[int, InTripDay] = {}
    activity_counters: dict[int, int] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 9:
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
    trip_uuid: str,
    pre_trip_phases: list[PreTripPhase],
    in_trip_days: list[InTripDay],
) -> None:
    """Delete all existing phase data for the trip and insert fresh rows. Runs in a transaction."""
    async with conn.transaction():
        # 1. Delete traveler progress and all phase content for this trip
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

        # 2. Insert pre-trip phases — order comes from the spreadsheet
        sort_order = 0
        for phase in pre_trip_phases:
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


async def import_one(sheets_svc, conn: asyncpg.Connection, trip_uuid: str, sheet_id: str) -> dict:
    """Import a single trip. Returns a summary dict. Sheets tabs are read once and filtered."""
    viagens_rows = read_tab(sheets_svc, sheet_id, "Viagens")
    service_agreement_url = parse_service_agreement_url(viagens_rows, trip_uuid)

    fases_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Fases"), trip_uuid)
    pre_trip_phases = parse_fases_tab(fases_rows)

    checklist_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Checklist"), trip_uuid)
    parse_checklist_tab(checklist_rows, pre_trip_phases)

    links_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Links"), trip_uuid)
    parse_links_tab(links_rows, pre_trip_phases)

    roteiro_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Roteiro"), trip_uuid)
    in_trip_days = parse_roteiro_tab(roteiro_rows)

    if not pre_trip_phases and not in_trip_days:
        return {"skipped": True}

    await write_to_db(conn, trip_uuid, pre_trip_phases, in_trip_days)

    # Update service_agreement_url on the trip record
    await conn.execute(
        "UPDATE wetravel_trips SET service_agreement_url = $1 WHERE trip_uuid = $2",
        service_agreement_url, trip_uuid,
    )

    return {
        "skipped": False,
        "phases": len(pre_trip_phases),
        "checklist": sum(len(p.checklist) for p in pre_trip_phases),
        "links": sum(len(p.links) for p in pre_trip_phases),
        "days": len(in_trip_days),
        "activities": sum(len(d.activities) for d in in_trip_days),
        "service_agreement_url": service_agreement_url or "(none)",
    }


async def fetch_all_trip_uuids(conn: asyncpg.Connection) -> list[str]:
    rows = await conn.fetch("SELECT trip_uuid FROM wetravel_trips ORDER BY start_date NULLS LAST")
    return [r["trip_uuid"] for r in rows]


async def main(trip_uuids: list[str], sheet_id: str) -> None:
    if not sheet_id:
        print("ERROR: TRIP_CONTENT_SHEET_ID is not set in backend/.env")
        print("Run create_trip_sheets.py first and add the printed sheet ID to .env")
        sys.exit(1)

    print("Connecting to Google Sheets...")
    sheets_svc = build_sheets_client()

    print("Connecting to database...")
    conn = await asyncpg.connect(PG_URL)

    totals = {"phases": 0, "checklist": 0, "links": 0, "days": 0, "activities": 0}
    skipped = []
    failed = []

    try:
        for trip_uuid in trip_uuids:
            print(f"\n▶  {trip_uuid}")
            try:
                result = await import_one(sheets_svc, conn, trip_uuid, sheet_id)
                if result["skipped"]:
                    print(f"   ⏭  No data in sheet — skipped")
                    skipped.append(trip_uuid)
                else:
                    print(f"   ✅ {result['phases']} phases, {result['checklist']} checklist, {result['links']} links, {result['days']} days, {result['activities']} activities")
                    for k in totals:
                        totals[k] += result[k]
            except Exception as exc:
                print(f"   ❌ Failed: {exc}")
                failed.append(trip_uuid)
    finally:
        await conn.close()

    print(f"\n{'='*50}")
    print(f"Import complete — {len(trip_uuids)} trip(s) processed")
    print(f"  Imported : {len(trip_uuids) - len(skipped) - len(failed)}")
    print(f"  Skipped  : {len(skipped)}")
    print(f"  Failed   : {len(failed)}")
    if failed:
        print(f"  Failed UUIDs: {failed}")
    print(f"\nTotals:")
    for k, v in totals.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import trip content from the shared Google Sheets spreadsheet into Supabase"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--trip-uuid",
        help="Import a single trip UUID",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Import all trips from wetravel_trips",
    )
    parser.add_argument(
        "--sheet-id",
        default=TRIP_CONTENT_SHEET_ID,
        help="Override the spreadsheet ID (default: TRIP_CONTENT_SHEET_ID from .env)",
    )
    args = parser.parse_args()

    async def _run():
        if args.all:
            conn = await asyncpg.connect(PG_URL)
            try:
                uuids = await fetch_all_trip_uuids(conn)
            finally:
                await conn.close()
            print(f"Found {len(uuids)} trips: {uuids}")
        else:
            uuids = [args.trip_uuid]
        await main(uuids, args.sheet_id)

    asyncio.run(_run())

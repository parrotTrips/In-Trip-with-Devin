"""Admin service: import trip content, reset content, reset traveler progress."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Allow importing from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

load_dotenv(Path(__file__).parent.parent.parent / ".env")

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


async def _get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(PG_URL)


async def admin_set_mode(trip_uuid: str, mode: str) -> dict:
    """Set the trip mode ('pre-trip' or 'in-trip') in trip_settings."""
    if mode not in ("pre-trip", "in-trip"):
        raise ValueError(f"Invalid mode '{mode}'. Must be 'pre-trip' or 'in-trip'.")
    conn = await _get_connection()
    try:
        await conn.execute(
            """
            INSERT INTO trip_settings (trip_uuid, mode)
            VALUES ($1, $2)
            ON CONFLICT (trip_uuid) DO UPDATE SET mode = $2, updated_at = now()
            """,
            trip_uuid, mode,
        )
    finally:
        await conn.close()
    return {"status": "ok", "trip_uuid": trip_uuid, "mode": mode}


async def admin_list_trips() -> dict:
    """Return all active trips (end_date >= today or end_date is null) ordered by start_date."""
    conn = await _get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT trip_uuid, title, start_date, end_date
            FROM wetravel_trips
            WHERE end_date IS NULL OR end_date::date >= CURRENT_DATE
            ORDER BY start_date NULLS LAST
            """
        )
    finally:
        await conn.close()

    return {
        "trips": [
            {
                "trip_uuid": r["trip_uuid"],
                "title": r["title"] or "",
                "start_date": str(r["start_date"])[:10] if r["start_date"] else "",
                "end_date": str(r["end_date"])[:10] if r["end_date"] else "",
            }
            for r in rows
        ]
    }


def _build_sheets_client_adc():
    """Build a Sheets client using Application Default Credentials (works in Cloud Run)."""
    import google.auth
    from googleapiclient.discovery import build as gapi_build
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds, _ = google.auth.default(scopes=SCOPES)
    return gapi_build("sheets", "v4", credentials=creds)


async def admin_import_trip(trip_uuid: str) -> dict:
    """Import trip content from Google Sheets into Supabase."""
    from scripts.import_trip_content import (
        filter_rows_by_trip,
        parse_checklist_tab,
        parse_fases_tab,
        parse_links_tab,
        parse_roteiro_tab,
        read_tab,
        write_to_db,
    )

    if not TRIP_CONTENT_SHEET_ID:
        raise ValueError("TRIP_CONTENT_SHEET_ID is not set")

    sheets_svc = _build_sheets_client_adc()

    fases_rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Fases"), trip_uuid)
    pre_trip_phases = parse_fases_tab(fases_rows)

    checklist_rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Checklist"), trip_uuid)
    parse_checklist_tab(checklist_rows, pre_trip_phases)

    links_rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Links"), trip_uuid)
    parse_links_tab(links_rows, pre_trip_phases)

    roteiro_rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Roteiro"), trip_uuid)
    in_trip_days = parse_roteiro_tab(roteiro_rows)

    if not pre_trip_phases and not in_trip_days:
        return {"status": "skipped", "message": f"No data found for trip '{trip_uuid}' in the sheet"}

    conn = await _get_connection()
    try:
        await write_to_db(conn, trip_uuid, pre_trip_phases, in_trip_days)
    finally:
        await conn.close()

    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "phases": len(pre_trip_phases),
        "checklist_items": sum(len(p.checklist) for p in pre_trip_phases),
        "links": sum(len(p.links) for p in pre_trip_phases),
        "days": len(in_trip_days),
        "activities": sum(len(d.activities) for d in in_trip_days),
    }


async def admin_reset_content(trip_uuid: str) -> dict:
    """Delete all trip_phases and child rows for the given trip."""
    conn = await _get_connection()
    try:
        phase_rows = await conn.fetch(
            "SELECT id FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if not phase_rows:
            return {"status": "ok", "message": "No content to delete", "deleted_phases": 0}

        phase_ids = [str(r["id"]) for r in phase_rows]
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        async with conn.transaction():
            if tt_rows:
                tt_ids = [str(r["id"]) for r in tt_rows]
                await conn.execute(
                    "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
                await conn.execute(
                    "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
            await conn.execute(
                "DELETE FROM trip_activities WHERE trip_phase_id = ANY($1::uuid[])", phase_ids
            )
            await conn.execute(
                "DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = ANY($1::uuid[])", phase_ids
            )
            await conn.execute(
                "DELETE FROM trip_phase_links WHERE trip_phase_id = ANY($1::uuid[])", phase_ids
            )
            await conn.execute(
                "DELETE FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
            )
    finally:
        await conn.close()

    return {"status": "ok", "trip_uuid": trip_uuid, "deleted_phases": len(phase_ids)}


async def admin_reset_progress(trip_uuid: str) -> dict:
    """Delete all traveler progress (checklist + phase) for the given trip."""
    conn = await _get_connection()
    try:
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if not tt_rows:
            return {"status": "ok", "message": "No travelers found", "deleted_rows": 0}

        tt_ids = [str(r["id"]) for r in tt_rows]
        async with conn.transaction():
            deleted_checklist = await conn.fetchval(
                "WITH d AS (DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[]) RETURNING 1) SELECT COUNT(*) FROM d",
                tt_ids,
            )
            deleted_phase = await conn.fetchval(
                "WITH d AS (DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[]) RETURNING 1) SELECT COUNT(*) FROM d",
                tt_ids,
            )
    finally:
        await conn.close()

    # Switch trip to in-trip mode
    conn2 = await _get_connection()
    try:
        await conn2.execute(
            """
            INSERT INTO trip_settings (trip_uuid, mode)
            VALUES ($1, 'in-trip')
            ON CONFLICT (trip_uuid) DO UPDATE SET mode = 'in-trip', updated_at = now()
            """,
            trip_uuid,
        )
    finally:
        await conn2.close()

    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "mode": "in-trip",
        "deleted_checklist_progress": deleted_checklist,
        "deleted_phase_progress": deleted_phase,
    }

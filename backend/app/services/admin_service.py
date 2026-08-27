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
STAFF_CONTENT_SHEET_ID = os.environ.get("STAFF_CONTENT_SHEET_ID", "")


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
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds, _ = google.auth.default(scopes=SCOPES)
    return gapi_build("sheets", "v4", credentials=creds)


async def admin_sync_roteiro_to_sheet(trip_uuid: str) -> dict:
    """Write address and max_checkins from DB back to the Roteiro sheet tab."""
    if not TRIP_CONTENT_SHEET_ID:
        raise ValueError("TRIP_CONTENT_SHEET_ID is not set")

    sheets_svc = _build_sheets_client_adc()

    # Read current Roteiro tab to find header and row positions
    resp = (
        sheets_svc.spreadsheets()
        .values()
        .get(spreadsheetId=TRIP_CONTENT_SHEET_ID, range="Roteiro")
        .execute()
    )
    rows = resp.get("values", [])
    if not rows:
        return {"status": "skipped", "message": "Roteiro tab is empty"}

    header = [h.strip().lower() for h in rows[0]]
    def find_col(names):
        for n in names:
            try:
                return header.index(n)
            except ValueError:
                pass
        return None

    endereco_col = find_col(["atividade_endereco", "endereco"])
    max_scans_col = find_col(["max_scans", "atividade_max_scans"])
    atividade_col = find_col(["atividade_nome", "atividade"])
    trip_uuid_col = find_col(["trip_uuid"])

    if None in (endereco_col, max_scans_col, atividade_col, trip_uuid_col):
        missing = [n for n, c in [("endereco", endereco_col), ("max_scans", max_scans_col), ("atividade_nome", atividade_col), ("trip_uuid", trip_uuid_col)] if c is None]
        return {"status": "error", "message": f"Columns not found: {missing}. Header: {header}"}

    # Fetch DB values
    conn = await _get_connection()
    try:
        db_rows = await conn.fetch("""
            SELECT ta.name, ta.address, ta.max_checkins
            FROM trip_activities ta
            JOIN trip_phases tp ON tp.id = ta.trip_phase_id
            WHERE tp.wetravel_trip_uuid = $1 AND tp.phase_type = 'in-trip'
        """, trip_uuid)
    finally:
        await conn.close()

    db_map = {r["name"]: r for r in db_rows}

    # Build batch update — write address and max_scans into each matching row
    updates = []
    for i, row in enumerate(rows[1:], start=2):  # 1-indexed, skip header
        if len(row) <= trip_uuid_col:
            continue
        if row[trip_uuid_col].strip() != trip_uuid:
            continue
        act_name = row[atividade_col].strip() if atividade_col < len(row) else ""
        if not act_name or act_name not in db_map:
            continue
        db = db_map[act_name]
        # Address cell
        updates.append({
            "range": f"Roteiro!{chr(65 + endereco_col)}{i}",
            "values": [[db["address"] or ""]],
        })
        # max_scans cell
        updates.append({
            "range": f"Roteiro!{chr(65 + max_scans_col)}{i}",
            "values": [[str(db["max_checkins"]) if db["max_checkins"] > 1 else ""]],
        })

    if not updates:
        return {"status": "skipped", "message": "No matching rows found"}

    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=TRIP_CONTENT_SHEET_ID,
        body={"valueInputOption": "RAW", "data": updates},
    ).execute()

    return {"status": "ok", "trip_uuid": trip_uuid, "cells_updated": len(updates)}


def _ensure_sheet_tab(sheets_svc, spreadsheet_id: str, tab_name: str) -> None:
    """Create a Google Sheets tab if it is missing."""
    spreadsheet = (
        sheets_svc.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
        .execute()
    )
    titles = {
        sheet.get("properties", {}).get("title")
        for sheet in spreadsheet.get("sheets", [])
    }
    if tab_name in titles:
        return

    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
    ).execute()


async def admin_sync_feedback_to_sheet(trip_uuid: str) -> dict:
    """Write traveler app feedback submissions from DB to the Trip Content Google Sheet."""
    if not TRIP_CONTENT_SHEET_ID:
        raise ValueError("TRIP_CONTENT_SHEET_ID is not set")

    conn = await _get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT
                taf.id::text AS feedback_id,
                tt.wetravel_trip_uuid AS trip_uuid,
                COALESCE(u.full_name, '') AS traveler_name,
                COALESCE(u.phone, '') AS phone,
                taf.feedback,
                taf.created_at::text AS created_at
            FROM traveler_app_feedback taf
            JOIN trip_travelers tt ON tt.id = taf.trip_traveler_id
            JOIN users u ON u.id = tt.user_id
            WHERE tt.wetravel_trip_uuid = $1
            ORDER BY taf.created_at, taf.id
            """,
            trip_uuid,
        )
    finally:
        await conn.close()

    data = [["feedback_id", "trip_uuid", "traveler_name", "phone", "feedback", "created_at"]]
    for r in rows:
        data.append([
            r["feedback_id"],
            r["trip_uuid"],
            r["traveler_name"],
            r["phone"],
            r["feedback"],
            r["created_at"],
        ])

    sheets_svc = _build_sheets_client_adc()
    _ensure_sheet_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Feedbacks")
    sheets_svc.spreadsheets().values().clear(
        spreadsheetId=TRIP_CONTENT_SHEET_ID,
        range="Feedbacks",
    ).execute()
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=TRIP_CONTENT_SHEET_ID,
        range="Feedbacks!A1",
        valueInputOption="RAW",
        body={"values": data},
    ).execute()

    return {"status": "ok", "trip_uuid": trip_uuid, "feedback_rows": len(rows)}


async def admin_setup_staff_sheet_headers() -> dict:
    """Add photo_url and bio columns to the Staff sheet header if missing."""
    if not STAFF_CONTENT_SHEET_ID:
        raise ValueError("STAFF_CONTENT_SHEET_ID is not set")

    sheets_svc = _build_sheets_client_adc()
    resp = (
        sheets_svc.spreadsheets()
        .values()
        .get(spreadsheetId=STAFF_CONTENT_SHEET_ID, range="Staff!1:1")
        .execute()
    )
    header = [h.strip().lower() for h in (resp.get("values") or [[]])[0]]

    updates = []
    next_col = len(header)
    added = []
    for col_name in ["photo_url", "bio"]:
        if col_name not in header:
            updates.append({
                "range": f"Staff!{chr(65 + next_col)}1",
                "values": [[col_name]],
            })
            next_col += 1
            added.append(col_name)

    if not updates:
        return {"status": "ok", "message": "Headers already present", "added": []}

    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=STAFF_CONTENT_SHEET_ID,
        body={"valueInputOption": "RAW", "data": updates},
    ).execute()

    return {"status": "ok", "added": added}


async def admin_write_staff_bios(trip_uuid: str, bios: dict) -> dict:
    """Write bio values into the Staff sheet tab for matching phone numbers."""
    if not STAFF_CONTENT_SHEET_ID:
        raise ValueError("STAFF_CONTENT_SHEET_ID is not set")

    sheets_svc = _build_sheets_client_adc()

    resp = (
        sheets_svc.spreadsheets()
        .values()
        .get(spreadsheetId=STAFF_CONTENT_SHEET_ID, range="Staff")
        .execute()
    )
    rows = resp.get("values", [])
    if not rows:
        return {"status": "error", "message": "Staff tab is empty"}

    header = [h.strip().lower() for h in rows[0]]

    def find_col(names):
        for n in names:
            try:
                return header.index(n)
            except ValueError:
                pass
        return None

    phone_col = find_col(["phone"])
    bio_col = find_col(["bio"])

    if phone_col is None or bio_col is None:
        return {"status": "error", "message": f"Columns not found. Header: {header}"}

    updates = []
    for i, row in enumerate(rows[1:], start=2):
        phone = row[phone_col].strip() if phone_col < len(row) else ""
        if phone in bios:
            updates.append({
                "range": f"Staff!{chr(65 + bio_col)}{i}",
                "values": [[bios[phone]]],
            })

    if not updates:
        return {"status": "skipped", "message": "No matching phones found"}

    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=STAFF_CONTENT_SHEET_ID,
        body={"valueInputOption": "RAW", "data": updates},
    ).execute()

    return {"status": "ok", "cells_updated": len(updates)}


async def admin_sync_staff_to_sheet(trip_uuid: str) -> dict:
    """Write staff tasks and activity participants from DB to the Staff Google Sheet."""
    if not STAFF_CONTENT_SHEET_ID:
        raise ValueError("STAFF_CONTENT_SHEET_ID is not set")

    sheets_svc = _build_sheets_client_adc()
    conn = await _get_connection()

    try:
        # --- Tarefas Staff ---
        task_rows = await conn.fetch("""
            SELECT u.phone, tp.sort_order as phase_order, ta.name as activity_name,
                   st.title, st.description, st.sort_order
            FROM staff_tasks st
            JOIN users u ON u.id = st.assigned_to_user_id
            JOIN trip_activities ta ON ta.id = st.trip_activity_id
            JOIN trip_phases tp ON tp.id = st.trip_phase_id
            WHERE tp.wetravel_trip_uuid = $1
            ORDER BY tp.sort_order, ta.sort_order, u.full_name
        """, trip_uuid)

        # phase_order starts at 4 for day 1 (4 pre-trip phases before in-trip)
        min_phase = min((r["phase_order"] for r in task_rows), default=4)

        tasks_data = [["trip_uuid", "dia", "atividade_nome", "staff_phone", "titulo", "descricao", "sort_order"]]
        for r in task_rows:
            day_num = r["phase_order"] - (min_phase - 1)
            tasks_data.append([
                trip_uuid,
                day_num,
                r["activity_name"],
                r["phone"],
                r["title"],
                r["description"] or "",
                r["sort_order"],
            ])

        # --- Participantes Atividades ---
        part_rows = await conn.fetch("""
            SELECT u.phone, tp.sort_order as phase_order, ta.name as activity_name, ap.status
            FROM activity_participants ap
            JOIN trip_travelers tt ON tt.id = ap.trip_traveler_id
            JOIN users u ON u.id = tt.user_id
            JOIN trip_activities ta ON ta.id = ap.trip_activity_id
            JOIN trip_phases tp ON tp.id = ta.trip_phase_id
            WHERE tt.wetravel_trip_uuid = $1
            ORDER BY tp.sort_order, ta.name
        """, trip_uuid)

        parts_data = [["trip_uuid", "dia", "atividade_nome", "traveler_phone", "status"]]
        for r in part_rows:
            day_num = r["phase_order"] - (min_phase - 1)
            parts_data.append([trip_uuid, day_num, r["activity_name"], r["phone"], r["status"]])

    finally:
        await conn.close()

    # Clear and write Tarefas Staff tab
    sheets_svc.spreadsheets().values().clear(
        spreadsheetId=STAFF_CONTENT_SHEET_ID, range="Tarefas Staff"
    ).execute()
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=STAFF_CONTENT_SHEET_ID,
        range="Tarefas Staff!A1",
        valueInputOption="RAW",
        body={"values": tasks_data},
    ).execute()

    # Clear and write Participantes Atividades tab
    sheets_svc.spreadsheets().values().clear(
        spreadsheetId=STAFF_CONTENT_SHEET_ID, range="Participantes Atividades"
    ).execute()
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=STAFF_CONTENT_SHEET_ID,
        range="Participantes Atividades!A1",
        valueInputOption="RAW",
        body={"values": parts_data},
    ).execute()

    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "tasks_written": len(tasks_data) - 1,
        "participants_written": len(parts_data) - 1,
    }


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


async def admin_start_trip(trip_uuid: str) -> dict:
    """Start the trip: clear phase progress, preserve checklist, switch to in-trip.

    Use this on the real trip start day. Travelers keep their pre-trip checklist
    completions; the progress bar resets to 0% and begins advancing by date.
    """
    conn = await _get_connection()
    try:
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if not tt_rows:
            return {"status": "ok", "message": "No travelers found", "deleted_rows": 0}

        tt_ids = [str(r["id"]) for r in tt_rows]
        async with conn.transaction():
            deleted_phase = await conn.fetchval(
                "WITH d AS (DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[]) RETURNING 1) SELECT COUNT(*) FROM d",
                tt_ids,
            )
            await conn.execute(
                """
                INSERT INTO trip_settings (trip_uuid, mode)
                VALUES ($1, 'in-trip')
                ON CONFLICT (trip_uuid) DO UPDATE SET mode = 'in-trip', updated_at = now()
                """,
                trip_uuid,
            )
    finally:
        await conn.close()

    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "mode": "in-trip",
        "deleted_phase_progress": deleted_phase,
    }


async def admin_reset_trip(trip_uuid: str) -> dict:
    """Full reset to pre-trip launch state: clears ALL progress (checklist + phase).

    Use this for testing — brings the trip back as if no traveler has touched
    anything. Not intended for production use on a live trip.
    """
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
            await conn.execute(
                """
                INSERT INTO trip_settings (trip_uuid, mode)
                VALUES ($1, 'pre-trip')
                ON CONFLICT (trip_uuid) DO UPDATE SET mode = 'pre-trip', updated_at = now()
                """,
                trip_uuid,
            )
    finally:
        await conn.close()

    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "mode": "pre-trip",
        "deleted_checklist_progress": deleted_checklist,
        "deleted_phase_progress": deleted_phase,
    }


async def admin_import_emergency_contacts(trip_uuid: str) -> dict:
    """Import emergency contacts from the Trip Content Google Sheet."""
    if not TRIP_CONTENT_SHEET_ID:
        raise ValueError("TRIP_CONTENT_SHEET_ID is not set")

    sheets_svc = _build_sheets_client_adc()

    from scripts.import_trip_content import filter_rows_by_trip, parse_recommendations_tab, read_tab

    rows = filter_rows_by_trip(
        read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Emergency Contacts"), trip_uuid
    )
    if not rows or len(rows) < 2:
        return {"status": "skipped", "message": "No emergency contacts found"}

    header = [h.strip().lower() for h in rows[0]]

    def col(row, name):
        try:
            idx = header.index(name)
            return row[idx].strip() if idx < len(row) else ""
        except ValueError:
            return ""

    contacts = []
    for row in rows[1:]:
        name = col(row, "name")
        if not name:
            continue
        try:
            sort_order = int(col(row, "sort_order") or "0")
        except ValueError:
            sort_order = 0
        contacts.append({
            "name": name,
            "role": col(row, "role") or None,
            "phone": col(row, "phone") or None,
            "sort_order": sort_order,
        })

    conn = await _get_connection()
    try:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM trip_emergency_contacts WHERE wetravel_trip_uuid = $1", trip_uuid
            )
            for c in contacts:
                await conn.execute(
                    """
                    INSERT INTO trip_emergency_contacts
                        (id, wetravel_trip_uuid, name, role, phone, sort_order, created_at, updated_at)
                    VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, now(), now())
                    """,
                    trip_uuid, c["name"], c["role"], c["phone"], c["sort_order"],
                )
    finally:
        await conn.close()

    return {"status": "ok", "trip_uuid": trip_uuid, "emergency_contacts_imported": len(contacts)}


async def admin_import_recommendations(trip_uuid: str) -> dict:
    """Import local recommendations from the Trip Content Google Sheet."""
    if not TRIP_CONTENT_SHEET_ID:
        raise ValueError("TRIP_CONTENT_SHEET_ID is not set")

    sheets_svc = _build_sheets_client_adc()

    from scripts.import_trip_content import filter_rows_by_trip, parse_recommendations_tab, read_tab

    rows = filter_rows_by_trip(
        read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Recomendacoes"), trip_uuid
    )
    if not rows or len(rows) < 2:
        return {"status": "skipped", "message": "No recommendations found"}

    recs = parse_recommendations_tab(rows)

    conn = await _get_connection()
    try:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM trip_recommendations WHERE wetravel_trip_uuid = $1", trip_uuid
            )
            for r in recs:
                await conn.execute(
                    """
                    INSERT INTO trip_recommendations
                        (
                            id, wetravel_trip_uuid, name, description, address, photo_url,
                            sort_order, category, neighborhood, location, highlight,
                            price_range, rating, map_url, emoji,
                            phone, whatsapp_url, contact_label, created_at, updated_at
                        )
                    VALUES (
                        gen_random_uuid(), $1, $2, $3, $4, $5,
                        $6, $7, $8, $9, $10,
                        $11, $12, $13, $14,
                        $15, $16, $17, now(), now()
                    )
                    """,
                    trip_uuid,
                    r.name,
                    r.description,
                    r.address,
                    r.photo_url,
                    r.sort_order,
                    r.category,
                    r.neighborhood,
                    r.location,
                    r.highlight,
                    r.price_range,
                    r.rating,
                    r.map_url,
                    r.emoji,
                    r.phone,
                    r.whatsapp_url,
                    r.contact_label,
                )
    finally:
        await conn.close()

    return {"status": "ok", "trip_uuid": trip_uuid, "recommendations_imported": len(recs)}


async def _import_simple_tab(trip_uuid: str, tab_name: str, table_name: str, columns: list[str]) -> dict:
    """Generic import for simple tabs — delete existing rows and insert fresh."""
    if not TRIP_CONTENT_SHEET_ID:
        raise ValueError("TRIP_CONTENT_SHEET_ID is not set")

    sheets_svc = _build_sheets_client_adc()
    from scripts.import_trip_content import filter_rows_by_trip, read_tab
    rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, tab_name), trip_uuid)
    if not rows or len(rows) < 2:
        return {"status": "skipped", "message": f"No data found in tab '{tab_name}'"}

    header = [h.strip().lower() for h in rows[0]]

    def col(row, name):
        try:
            idx = header.index(name)
            return row[idx].strip() if idx < len(row) else ""
        except ValueError:
            return ""

    records = []
    for row in rows[1:]:
        if not any(row):
            continue
        try:
            sort_order = int(col(row, "sort_order") or "0")
        except ValueError:
            sort_order = 0
        record = {c: col(row, c) or None for c in columns if c != "sort_order"}
        record["sort_order"] = sort_order
        if all(v is None for k, v in record.items() if k != "sort_order"):
            continue
        records.append(record)

    conn = await _get_connection()
    try:
        async with conn.transaction():
            await conn.execute(f"DELETE FROM {table_name} WHERE wetravel_trip_uuid = $1", trip_uuid)
            for r in records:
                cols = ["id", "wetravel_trip_uuid"] + list(r.keys()) + ["created_at", "updated_at"]
                placeholders = ["gen_random_uuid()", "$1"] + [f"${i+2}" for i in range(len(r))] + ["now()", "now()"]
                await conn.execute(
                    f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})",
                    trip_uuid, *r.values(),
                )
    finally:
        await conn.close()

    return {"status": "ok", "trip_uuid": trip_uuid, "imported": len(records)}


async def admin_import_faq(trip_uuid: str) -> dict:
    return await _import_simple_tab(trip_uuid, "FAQ", "trip_faqs", ["question", "answer", "sort_order"])


async def admin_import_cancellation_policy(trip_uuid: str) -> dict:
    return await _import_simple_tab(trip_uuid, "Cancellation Policy", "trip_cancellation_policies", ["title", "body", "sort_order"])


async def admin_import_contacts(trip_uuid: str) -> dict:
    """Import contacts from the Staff Google Sheet into trip_contacts."""
    if not STAFF_CONTENT_SHEET_ID:
        raise ValueError("STAFF_CONTENT_SHEET_ID is not set")

    from scripts.import_staff_content import (
        filter_rows_by_trip,
        parse_contacts_tab,
        read_tab,
        write_contacts,
    )

    sheets_svc = _build_sheets_client_adc()
    contacts_rows = filter_rows_by_trip(
        read_tab(sheets_svc, STAFF_CONTENT_SHEET_ID, "Contatos"), trip_uuid
    )
    contacts = parse_contacts_tab(contacts_rows)

    conn = await _get_connection()
    try:
        count = await write_contacts(conn, trip_uuid, contacts)
    finally:
        await conn.close()

    return {"status": "ok", "trip_uuid": trip_uuid, "contacts_imported": count}


async def admin_import_staff(trip_uuid: str) -> dict:
    """Import staff members from the Staff Google Sheet.

    For each row in the Staff tab:
    - Creates the user with role=staff if they don't exist yet
    - Updates name and role if they already exist
    - Links them to the trip via trip_travelers
    """
    if not STAFF_CONTENT_SHEET_ID:
        raise ValueError("STAFF_CONTENT_SHEET_ID is not set")

    from scripts.import_staff_content import (
        filter_rows_by_trip,
        parse_staff_tab,
        read_tab,
        write_staff,
    )

    sheets_svc = _build_sheets_client_adc()
    staff_rows = filter_rows_by_trip(
        read_tab(sheets_svc, STAFF_CONTENT_SHEET_ID, "Staff"), trip_uuid
    )
    members = parse_staff_tab(staff_rows)

    conn = await _get_connection()
    try:
        result = await write_staff(conn, trip_uuid, members)
    finally:
        await conn.close()

    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "staff_created": result["created"],
        "staff_updated": result["updated"],
        "staff_linked": result["linked"],
    }


async def admin_import_staff_tasks(trip_uuid: str) -> dict:
    """Import staff activity tasks from the Staff Google Sheet into staff_tasks."""
    if not STAFF_CONTENT_SHEET_ID:
        raise ValueError("STAFF_CONTENT_SHEET_ID is not set")

    from scripts.import_staff_content import (
        filter_rows_by_trip,
        parse_staff_tasks_tab,
        read_tab,
        write_staff_tasks,
    )

    sheets_svc = _build_sheets_client_adc()
    tasks_rows = filter_rows_by_trip(
        read_tab(sheets_svc, STAFF_CONTENT_SHEET_ID, "Tarefas Staff"), trip_uuid
    )
    tasks = parse_staff_tasks_tab(tasks_rows)

    conn = await _get_connection()
    try:
        count = await write_staff_tasks(conn, trip_uuid, tasks)
    finally:
        await conn.close()

    return {"status": "ok", "trip_uuid": trip_uuid, "staff_tasks_imported": count}


async def admin_import_activity_participants(trip_uuid: str) -> dict:
    """Import controlled activity participant allowlists from the Staff Google Sheet."""
    if not STAFF_CONTENT_SHEET_ID:
        raise ValueError("STAFF_CONTENT_SHEET_ID is not set")

    from scripts.import_staff_content import (
        filter_rows_by_trip,
        parse_activity_participants_tab,
        read_tab,
        write_activity_participants,
    )

    sheets_svc = _build_sheets_client_adc()
    participant_rows = filter_rows_by_trip(
        read_tab(sheets_svc, STAFF_CONTENT_SHEET_ID, "Participantes Atividades"), trip_uuid
    )
    participants = parse_activity_participants_tab(participant_rows)

    conn = await _get_connection()
    try:
        count = await write_activity_participants(conn, trip_uuid, participants)
    finally:
        await conn.close()

    return {"status": "ok", "trip_uuid": trip_uuid, "activity_participants_imported": count}


async def admin_set_user_role(phone: str, role: str) -> dict:
    """Set the role of a user identified by phone number."""
    if role not in ("traveler", "staff"):
        raise ValueError(f"Invalid role '{role}'. Must be 'traveler' or 'staff'.")

    conn = await _get_connection()
    try:
        result = await conn.fetchrow(
            "UPDATE users SET role = $1 WHERE phone = $2 RETURNING id, full_name, phone, role",
            role, phone,
        )
    finally:
        await conn.close()

    if not result:
        raise ValueError(f"No user found with phone '{phone}'")

    return {
        "status": "ok",
        "user_id": str(result["id"]),
        "name": result["full_name"],
        "phone": result["phone"],
        "role": result["role"],
    }

"""
Read the Staff Google Sheets spreadsheet and upsert staff content into Supabase.

Currently supports:
  - Aba "Contatos": trip_contacts table

The spreadsheet ID is read from STAFF_CONTENT_SHEET_ID in backend/.env.
This is a separate sheet from the traveler content sheet (TRIP_CONTENT_SHEET_ID).

Usage:
  cd backend

  # Import contacts for a specific trip:
  poetry run python scripts/import_staff_content.py --trip-uuid TEST-2026-FULL

  # Import contacts for all trips in the sheet:
  poetry run python scripts/import_staff_content.py --all

Prerequisites:
  - secrets/gcp-oauth2-credentials.json  (OAuth2 Desktop app client)
  - secrets/gcp-oauth2-token.json        (auto-created on first run)
  - DATABASE_URL and STAFF_CONTENT_SHEET_ID in backend/.env
"""

from __future__ import annotations

import argparse
import asyncio
import os
import uuid
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

STAFF_CONTENT_SHEET_ID = os.environ.get("STAFF_CONTENT_SHEET_ID", "")


# ── Sheets auth ───────────────────────────────────────────────────────────────

def _build_sheets_client() -> object:
    creds = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_OAUTH2_CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_FILE.write_text(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def read_tab(sheets_svc, sheet_id: str, tab_name: str) -> list[list[str]]:
    resp = (
        sheets_svc.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=tab_name)
        .execute()
    )
    return resp.get("values", [])


def filter_rows_by_trip(rows: list[list[str]], trip_uuid: str) -> list[list[str]]:
    if not rows:
        return []
    header = rows[0]
    matching = [row for row in rows[1:] if row and row[0].strip() == trip_uuid]
    return [header] + matching


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_contacts_tab(rows: list[list[str]]) -> list[dict]:
    """Parse Contatos tab. Returns list of contact dicts.
    Columns: trip_uuid, category, name, role, phone, sort_order
    """
    if not rows or len(rows) < 2:
        return []
    header = [h.strip().lower() for h in rows[0]]

    def col(row: list[str], name: str) -> str:
        try:
            idx = header.index(name)
            return row[idx].strip() if idx < len(row) else ""
        except ValueError:
            return ""

    contacts = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        name = col(row, "name")
        if not name:
            continue
        try:
            sort_order = int(col(row, "sort_order") or "0")
        except ValueError:
            sort_order = 0
        contacts.append({
            "trip_uuid": col(row, "trip_uuid"),
            "category": col(row, "category") or "Other",
            "name": name,
            "role": col(row, "role") or None,
            "phone": col(row, "phone") or None,
            "sort_order": sort_order,
        })
    return contacts


def parse_staff_tasks_tab(rows: list[list[str]]) -> list[dict]:
    """Parse Tarefas Staff tab.

    Columns: trip_uuid, dia, atividade_nome, staff_phone, titulo, descricao, sort_order
    """
    if not rows or len(rows) < 2:
        return []
    header = [h.strip().lower() for h in rows[0]]

    def col(row: list[str], name: str) -> str:
        try:
            idx = header.index(name)
            return row[idx].strip() if idx < len(row) else ""
        except ValueError:
            return ""

    tasks = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        title = col(row, "titulo")
        if not title:
            continue
        try:
            day = int(col(row, "dia") or "0")
        except ValueError:
            day = 0
        try:
            sort_order = int(col(row, "sort_order") or "0")
        except ValueError:
            sort_order = 0
        tasks.append({
            "trip_uuid": col(row, "trip_uuid"),
            "dia": day,
            "atividade_nome": col(row, "atividade_nome"),
            "staff_phone": col(row, "staff_phone"),
            "titulo": title,
            "descricao": col(row, "descricao") or None,
            "sort_order": sort_order,
        })
    return tasks


class StaffTaskImportError(ValueError):
    pass


def _require_single_row(rows: list, label: str, lookup: str):
    if len(rows) == 1:
        return rows[0]
    if not rows:
        raise StaffTaskImportError(f"{label} not found: {lookup}")
    raise StaffTaskImportError(f"{label} is ambiguous: {lookup}")


# ── DB write ──────────────────────────────────────────────────────────────────

async def write_contacts(conn: asyncpg.Connection, trip_uuid: str, contacts: list[dict]) -> int:
    """Delete existing contacts for trip and insert fresh rows."""
    await conn.execute(
        "DELETE FROM trip_contacts WHERE wetravel_trip_uuid = $1", trip_uuid
    )
    if not contacts:
        return 0
    for c in contacts:
        await conn.execute(
            """
            INSERT INTO trip_contacts
                (id, wetravel_trip_uuid, category, name, role, phone, sort_order, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, now(), now())
            """,
            str(uuid.uuid4()), trip_uuid, c["category"], c["name"],
            c["role"], c["phone"], c["sort_order"],
        )
    return len(contacts)


async def write_staff_tasks(conn: asyncpg.Connection, trip_uuid: str, tasks: list[dict]) -> int:
    """Delete existing staff tasks for a trip and insert fresh rows from the sheet."""
    async with conn.transaction():
        phase_rows = await conn.fetch(
            "SELECT id FROM trip_phases WHERE wetravel_trip_uuid = $1",
            trip_uuid,
        )
        phase_ids = [r["id"] for r in phase_rows]
        if phase_ids:
            await conn.execute(
                "DELETE FROM staff_tasks WHERE trip_phase_id = ANY($1::uuid[])",
                phase_ids,
            )

        inserted = 0
        for task in tasks:
            staff_rows = await conn.fetch(
                "SELECT id FROM users WHERE phone = $1 AND role = 'staff'",
                task["staff_phone"],
            )
            staff = _require_single_row(staff_rows, "staff", task["staff_phone"])

            day_rows = await conn.fetch(
                """
                SELECT id
                FROM trip_phases
                WHERE wetravel_trip_uuid = $1
                  AND phase_type = 'in-trip'
                  AND sort_order = $2
                """,
                trip_uuid,
                task["dia"] - 1,
            )
            day = _require_single_row(day_rows, "day", str(task["dia"]))

            activity_rows = await conn.fetch(
                """
                SELECT id
                FROM trip_activities
                WHERE trip_phase_id = $1
                  AND lower(name) = lower($2)
                """,
                day["id"],
                task["atividade_nome"],
            )
            activity = _require_single_row(activity_rows, "activity", task["atividade_nome"])

            await conn.execute(
                """
                INSERT INTO staff_tasks
                    (id, trip_phase_id, trip_activity_id, assigned_to_user_id,
                     title, description, starts_at, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NULL, $6, now(), now())
                """,
                day["id"],
                activity["id"],
                staff["id"],
                task["titulo"],
                task["descricao"],
                task["sort_order"],
            )
            inserted += 1

    return inserted


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_staff_tab(rows: list[list[str]]) -> list[dict]:
    """Parse Staff tab. Returns list of staff member dicts.
    Columns: phone, nome, funcao, trip_uuid
    """
    if not rows or len(rows) < 2:
        return []
    header = [h.strip().lower() for h in rows[0]]

    def col(row: list[str], name: str) -> str:
        try:
            idx = header.index(name)
            return row[idx].strip() if idx < len(row) else ""
        except ValueError:
            return ""

    members = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        phone = col(row, "phone")
        if not phone:
            continue
        members.append({
            "phone": phone,
            "nome": col(row, "nome") or None,
            "funcao": col(row, "funcao") or None,
            "trip_uuid": col(row, "trip_uuid"),
        })
    return members


async def write_staff(conn: asyncpg.Connection, trip_uuid: str, members: list[dict]) -> dict:
    """Upsert staff members: create user with role=staff if not exists, link to trip."""
    created = updated = linked = 0

    async with conn.transaction():
        for m in members:
            phone = m["phone"]
            name = m["nome"]

            # Upsert user — create with role=staff if not exists, update name/role if exists
            existing = await conn.fetchrow(
                "SELECT id, full_name, role FROM users WHERE phone = $1", phone
            )
            if existing:
                if existing["role"] != "staff" or (name and existing["full_name"] != name):
                    await conn.execute(
                        "UPDATE users SET role = 'staff', full_name = COALESCE($1, full_name), updated_at = now() WHERE phone = $2",
                        name, phone,
                    )
                    updated += 1
                user_id = existing["id"]
            else:
                user_id = await conn.fetchval(
                    """
                    INSERT INTO users (id, phone, full_name, role, created_at, updated_at)
                    VALUES (gen_random_uuid(), $1, $2, 'staff', now(), now())
                    RETURNING id
                    """,
                    phone, name,
                )
                created += 1

            # Link to trip via trip_travelers (upsert)
            existing_link = await conn.fetchrow(
                "SELECT id FROM trip_travelers WHERE user_id = $1 AND wetravel_trip_uuid = $2",
                user_id, trip_uuid,
            )
            if not existing_link:
                await conn.execute(
                    """
                    INSERT INTO trip_travelers (id, user_id, wetravel_trip_uuid, created_at, updated_at)
                    VALUES (gen_random_uuid(), $1, $2, now(), now())
                    """,
                    user_id, trip_uuid,
                )
                linked += 1

    return {"created": created, "updated": updated, "linked": linked}


async def import_one(sheets_svc, conn: asyncpg.Connection, trip_uuid: str, sheet_id: str) -> dict:
    contacts_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Contatos"), trip_uuid)
    contacts = parse_contacts_tab(contacts_rows)

    staff_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Staff"), trip_uuid)
    members = parse_staff_tab(staff_rows)

    tasks_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Tarefas Staff"), trip_uuid)
    tasks = parse_staff_tasks_tab(tasks_rows)

    if not contacts and not members and not tasks:
        return {"skipped": True, "trip_uuid": trip_uuid}

    async with conn.transaction():
        contacts_count = await write_contacts(conn, trip_uuid, contacts)
        staff_result = await write_staff(conn, trip_uuid, members)
        tasks_count = await write_staff_tasks(conn, trip_uuid, tasks)

    return {
        "skipped": False,
        "trip_uuid": trip_uuid,
        "contacts": contacts_count,
        "staff_tasks": tasks_count,
        "staff_created": staff_result["created"],
        "staff_updated": staff_result["updated"],
        "staff_linked": staff_result["linked"],
    }


async def main(trip_uuids: list[str], sheet_id: str) -> None:
    if not sheet_id:
        print("ERROR: STAFF_CONTENT_SHEET_ID not set in .env")
        return

    sheets_svc = _build_sheets_client()
    conn = await asyncpg.connect(PG_URL)
    try:
        for trip_uuid in trip_uuids:
            print(f"\nImporting contacts for trip: {trip_uuid}")
            result = await import_one(sheets_svc, conn, trip_uuid, sheet_id)
            if result.get("skipped"):
                print(f"  ⬜ No contacts found — skipped")
            else:
                print(f"  ✅ {result['contacts']} contacts imported")
                print(f"  ✅ {result['staff_tasks']} staff tasks imported")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import staff content from Google Sheets")
    parser.add_argument("--trip-uuid", help="Import for a specific trip UUID")
    parser.add_argument("--all", action="store_true", help="Import for all trips in the sheet")
    args = parser.parse_args()

    if not args.trip_uuid and not args.all:
        parser.error("Provide --trip-uuid <uuid> or --all")

    if args.trip_uuid:
        trip_uuids = [args.trip_uuid]
    else:
        # Read all trip_uuids from the Contatos tab
        sheets_svc = _build_sheets_client()
        rows = read_tab(sheets_svc, STAFF_CONTENT_SHEET_ID, "Contatos")
        seen: set[str] = set()
        trip_uuids = []
        for row in rows[1:]:
            if row and row[0].strip() and row[0].strip() not in seen:
                seen.add(row[0].strip())
                trip_uuids.append(row[0].strip())

    asyncio.run(main(trip_uuids, STAFF_CONTENT_SHEET_ID))

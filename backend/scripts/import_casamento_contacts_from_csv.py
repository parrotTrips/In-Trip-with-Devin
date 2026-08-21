"""Import wedding contacts from the root CSV into the GaRapha trip.

The script is dry-run by default. Use --execute to write to the database.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
CSV_PATH = REPO_ROOT / "contatos telefone app - casamento - Planilha3.csv"
TRIP_UUID = "CASAMENTO-GARAPHA-2026"
EXCLUDED = {("VITOR", "+5511997666680")}
AUDIT_TAB = "Viajantes Teste"
AUDIT_HEADER = [
    "trip_uuid",
    "full_name",
    "preferred_name",
    "phone",
    "email",
    "package_name",
    "room_type",
    "paid_amount_usd",
    "addons",
    "user_id",
    "trip_traveler_id",
    "qr_filename",
    "qr_drive_url",
]
STAFF_TAB = "Staff"
STAFF_HEADER = ["phone", "nome", "funcao", "trip_uuid", "photo_url", "bio"]
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
OAUTH_TOKEN_FILE = BACKEND_ROOT / "secrets" / "gcp-oauth2-token.json"
OAUTH_CLIENT_FILE = BACKEND_ROOT / "secrets" / "gcp-oauth2-credentials.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Write changes to the database")
    parser.add_argument("--sync-sheets", action="store_true", help="Mirror current trip travelers to Google Sheets")
    parser.add_argument("--sheets-only", action="store_true", help="Only mirror current trip travelers to Google Sheets")
    parser.add_argument("--csv", default=str(CSV_PATH), help="CSV path")
    return parser.parse_args()


def load_database_url() -> str:
    load_dotenv(BACKEND_ROOT / ".env")
    database_url = os.environ["DATABASE_URL"]
    return database_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def clean(value: str | None) -> str:
    return (value or "").strip()


def normalize_phone(value: str | None) -> str:
    phone = clean(value)
    if not phone:
        return ""
    return phone if phone.startswith("+") else f"+{phone}"


def read_contacts(path: Path) -> list[dict[str, str]]:
    contacts: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    for row in rows[1:]:
        if len(row) < 4:
            continue
        name = clean(row[1])
        phone = normalize_phone(row[3])
        marker = clean(row[4]) if len(row) > 4 else ""
        if not name or not phone:
            continue
        if (name.upper(), phone) in EXCLUDED:
            continue
        contacts.append({"name": name, "phone": phone, "marker": marker})
    return contacts


async def existing_trip_links(conn: asyncpg.Connection) -> dict[str, dict[str, Any]]:
    rows = await conn.fetch(
        """
        select u.phone, u.full_name, u.role, tt.id as trip_traveler_id
        from trip_travelers tt
        join users u on u.id = tt.user_id
        where tt.wetravel_trip_uuid = $1
        """,
        TRIP_UUID,
    )
    return {row["phone"]: dict(row) for row in rows}


async def import_contacts(conn: asyncpg.Connection, contacts: list[dict[str, str]]) -> dict[str, Any]:
    now = datetime.now(UTC)
    inserted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    async with conn.transaction():
        for contact in contacts:
            existing = await conn.fetchrow(
                """
                select u.full_name, u.role, tt.id as trip_traveler_id
                from trip_travelers tt
                join users u on u.id = tt.user_id
                where tt.wetravel_trip_uuid = $1 and u.phone = $2
                """,
                TRIP_UUID,
                contact["phone"],
            )
            if existing:
                skipped.append(
                    {
                        **contact,
                        "existing_name": existing["full_name"],
                        "existing_role": existing["role"],
                        "reason": "already_in_trip",
                    }
                )
                continue

            user_id = await conn.fetchval(
                """
                insert into users (id, phone, full_name, email, status, role, created_at, updated_at)
                values ($1, $2, $3, null, 'active', 'traveler', $4, $4)
                on conflict (phone) do update
                set full_name = case
                        when users.full_name is null or users.full_name = ''
                        then excluded.full_name
                        else users.full_name
                    end,
                    status = 'active',
                    role = case when users.role = 'staff' then users.role else 'traveler' end,
                    updated_at = excluded.updated_at
                returning id
                """,
                uuid.uuid4(),
                contact["phone"],
                contact["name"],
                now,
            )
            trip_traveler_id = await conn.fetchval(
                """
                insert into trip_travelers (id, wetravel_trip_uuid, user_id, created_at, updated_at)
                values ($1, $2, $3, $4, $4)
                on conflict (wetravel_trip_uuid, user_id) do update
                set updated_at = excluded.updated_at
                returning id
                """,
                uuid.uuid4(),
                TRIP_UUID,
                user_id,
                now,
            )
            await conn.execute(
                """
                insert into traveler_profiles (
                    id, trip_traveler_id, preferred_name, plus_one_flag,
                    needs_flight_help_flag, needs_travel_insurance_help_flag,
                    unforgettable_trip_details, created_at, updated_at
                )
                values ($1, $2, $3, false, false, false, $4, $5, $5)
                on conflict (trip_traveler_id) do update
                set preferred_name = coalesce(traveler_profiles.preferred_name, excluded.preferred_name),
                    updated_at = excluded.updated_at
                """,
                uuid.uuid4(),
                trip_traveler_id,
                contact["name"],
                "Casamento Gabriela e Raphael - contato importado do CSV de convidados.",
                now,
            )
            await conn.execute(
                """
                insert into traveler_products (id, trip_traveler_id, room_type, created_at, updated_at)
                values ($1, $2, 'Wedding Guest', $3, $3)
                on conflict (trip_traveler_id) do update
                set room_type = coalesce(traveler_products.room_type, excluded.room_type),
                    updated_at = excluded.updated_at
                """,
                uuid.uuid4(),
                trip_traveler_id,
                now,
            )
            inserted.append(
                {
                    **contact,
                    "user_id": str(user_id),
                    "trip_traveler_id": str(trip_traveler_id),
                }
            )

    return {"inserted": inserted, "skipped": skipped}


async def fetch_traveler_audit_rows(conn: asyncpg.Connection) -> list[list[Any]]:
    rows = await conn.fetch(
        """
        select
            u.full_name,
            tp.preferred_name,
            u.phone,
            u.email,
            u.id as user_id,
            tt.id as trip_traveler_id,
            tprod.room_type
        from trip_travelers tt
        join users u on u.id = tt.user_id
        left join traveler_profiles tp on tp.trip_traveler_id = tt.id
        left join traveler_products tprod on tprod.trip_traveler_id = tt.id
        where tt.wetravel_trip_uuid = $1
          and u.role = 'traveler'
        order by u.full_name, u.phone
        """,
        TRIP_UUID,
    )
    return [
        [
            TRIP_UUID,
            row["full_name"] or "",
            row["preferred_name"] or row["full_name"] or "",
            row["phone"] or "",
            row["email"] or "",
            "Wedding Guest",
            row["room_type"] or "Wedding Guest",
            "",
            "none",
            str(row["user_id"]),
            str(row["trip_traveler_id"]),
            "",
            "",
        ]
        for row in rows
    ]


async def fetch_staff_rows(conn: asyncpg.Connection) -> list[list[Any]]:
    rows = await conn.fetch(
        """
        select
            u.phone,
            u.full_name,
            ts.function,
            ts.photo_url,
            ts.bio
        from trip_staff ts
        join users u on u.id = ts.user_id
        where ts.wetravel_trip_uuid = $1
        order by u.full_name, u.phone
        """,
        TRIP_UUID,
    )
    return [
        [
            row["phone"] or "",
            row["full_name"] or "",
            row["function"] or "Internal Staff / Traveler Support",
            TRIP_UUID,
            row["photo_url"] or "",
            row["bio"] or "",
        ]
        for row in rows
    ]


def normalize_sheet_values(rows: list[list[Any]]) -> list[list[Any]]:
    return [["" if value is None else value for value in row] for row in rows]


def build_sheets_client():
    credentials = None
    if OAUTH_TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(str(OAUTH_TOKEN_FILE), GOOGLE_SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not OAUTH_CLIENT_FILE.exists():
                raise RuntimeError(f"OAuth client file not found: {OAUTH_CLIENT_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT_FILE), GOOGLE_SCOPES)
            credentials = flow.run_local_server(port=0)
        OAUTH_TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return build("sheets", "v4", credentials=credentials)


def get_tab_properties(sheets, spreadsheet_id: str) -> dict[str, dict[str, Any]]:
    meta = (
        sheets.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties(sheetId,title)")
        .execute()
    )
    return {sheet["properties"]["title"]: sheet["properties"] for sheet in meta.get("sheets", [])}


def ensure_tab(sheets, spreadsheet_id: str, tab: str) -> None:
    if tab in get_tab_properties(sheets, spreadsheet_id):
        return
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
    ).execute()


def row_matches_trip_uuid(row: list[Any], header: list[str]) -> bool:
    try:
        trip_uuid_index = [str(value).strip().lower() for value in header].index("trip_uuid")
    except ValueError:
        return False
    return trip_uuid_index < len(row) and str(row[trip_uuid_index]).strip() == TRIP_UUID


def replace_trip_rows(sheets, spreadsheet_id: str, tab: str, header: list[str], new_rows: list[list[Any]]) -> int:
    ensure_tab(sheets, spreadsheet_id, tab)
    existing = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"'{tab}'!A:Z")
        .execute()
        .get("values", [])
    )
    existing_header = existing[0] if existing else header
    if existing_header != header:
        raise ValueError(f"Header mismatch for {tab}: expected {header}, found {existing_header}")
    kept_rows = [row for row in existing[1:] if not row_matches_trip_uuid(row, existing_header)]
    merged = normalize_sheet_values([header] + kept_rows + new_rows)
    sheets.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"'{tab}'!A:Z",
    ).execute()
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{tab}'!A1",
        valueInputOption="RAW",
        body={"values": merged},
    ).execute()
    return len(new_rows)


async def sync_sheets(conn: asyncpg.Connection) -> dict[str, Any]:
    load_dotenv(BACKEND_ROOT / ".env")
    sheet_ids = {
        "content": os.environ.get("TRIP_CONTENT_SHEET_ID", ""),
        "staff": os.environ.get("STAFF_CONTENT_SHEET_ID", ""),
    }
    missing = [name for name, sheet_id in sheet_ids.items() if not sheet_id]
    if missing:
        raise RuntimeError(f"Missing sheet ids: {', '.join(missing)}")

    traveler_rows = await fetch_traveler_audit_rows(conn)
    staff_rows = await fetch_staff_rows(conn)
    sheets = build_sheets_client()
    traveler_updated = {
        name: replace_trip_rows(sheets, sheet_id, AUDIT_TAB, AUDIT_HEADER, traveler_rows)
        for name, sheet_id in sheet_ids.items()
    }
    staff_updated = replace_trip_rows(
        sheets,
        sheet_ids["staff"],
        STAFF_TAB,
        STAFF_HEADER,
        staff_rows,
    )
    return {
        "traveler_tab": AUDIT_TAB,
        "traveler_rows": len(traveler_rows),
        "traveler_updated": traveler_updated,
        "staff_tab": STAFF_TAB,
        "staff_rows": len(staff_rows),
        "staff_updated": staff_updated,
    }


async def main() -> None:
    args = parse_args()
    contacts = read_contacts(Path(args.csv))
    conn = await asyncpg.connect(load_database_url())
    try:
        if args.sheets_only:
            print(json.dumps({"mode": "sheets-only", "sheets": await sync_sheets(conn)}, indent=2))
            return

        existing = await existing_trip_links(conn)
        to_insert = [contact for contact in contacts if contact["phone"] not in existing]
        skipped = [
            {
                **contact,
                "existing_name": existing[contact["phone"]]["full_name"],
                "existing_role": existing[contact["phone"]]["role"],
                "reason": "already_in_trip",
            }
            for contact in contacts
            if contact["phone"] in existing
        ]
        if not args.execute:
            print(
                json.dumps(
                    {
                        "mode": "dry-run",
                        "contacts_after_excluding_vitor": len(contacts),
                        "would_insert": len(to_insert),
                        "would_skip_existing": skipped,
                    },
                    indent=2,
                    default=str,
                )
            )
            return
        result = await import_contacts(conn, contacts)
        sheets_result = await sync_sheets(conn) if args.sync_sheets else None
        print(
            json.dumps(
                {
                    "mode": "execute",
                    "inserted": len(result["inserted"]),
                    "skipped_existing": result["skipped"],
                    "sheets": sheets_result,
                },
                indent=2,
                default=str,
            )
        )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

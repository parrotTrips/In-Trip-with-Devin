"""Seed the minimal app data for Casamento Gabriela e Raphael.

Default mode is dry-run. Use --execute to write to Supabase and Google Sheets.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg
from dotenv import load_dotenv


TRIP_UUID = "CASAMENTO-GARAPHA-2026"
TRIP = {
    "title": "Casamento Gabriela e Raphael",
    "destination": "Prea, Ceara, Brasil",
    "start_date": "2026-09-04",
    "end_date": "2026-09-06",
    "url": "https://sites.icasei.com.br/gabrielaeraphael/home",
    "service_agreement_url": "",
}
TRAVELERS = [
    {
        "full_name": "Gabriela",
        "preferred_name": "Gabriela",
        "phone": "+5534991825752",
        "email": "",
    },
    {
        "full_name": "Raphael",
        "preferred_name": "Raphael",
        "phone": "+5511993741189",
        "email": "",
    },
]

AUDIT_TAB = "Viajantes Teste"
CONTENT_TABS = {
    "Viagens": ["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim", "service_agreement_url"],
    AUDIT_TAB: [
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
    ],
}
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "outputs/casamento-garapha"
OAUTH_TOKEN_FILE = BACKEND_ROOT / "secrets" / "gcp-oauth2-token.json"
OAUTH_CLIENT_FILE = BACKEND_ROOT / "secrets" / "gcp-oauth2-credentials.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Write to Supabase and Google Sheets")
    parser.add_argument("--skip-sheets", action="store_true", help="Do not update Google Sheets")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Audit output directory")
    return parser.parse_args(argv)


def load_database_url() -> str:
    load_dotenv(BACKEND_ROOT / ".env")
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return database_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def build_dry_run_summary() -> dict[str, Any]:
    return {
        "trip_uuid": TRIP_UUID,
        "would_create_or_update": {
            "wetravel_trips": 1,
            "trip_settings": 1,
            "users": len(TRAVELERS),
            "trip_travelers": len(TRAVELERS),
            "traveler_profiles": len(TRAVELERS),
            "traveler_products": len(TRAVELERS),
            "sheet_trip_rows": 1,
            "sheet_traveler_rows": len(TRAVELERS),
        },
    }


def build_wetravel_trip_record(now: datetime) -> dict[str, Any]:
    return {
        "id": uuid.uuid4(),
        "entity_key": TRIP_UUID,
        "event_type": "manual_seed",
        "event_received_at": now,
        "trip_uuid": TRIP_UUID,
        "trip_id": TRIP_UUID,
        "title": TRIP["title"],
        "destination": TRIP["destination"],
        "currency": "BRL",
        "url": TRIP["url"],
        "listing_status": "manual",
        "start_date": TRIP["start_date"],
        "end_date": TRIP["end_date"],
        "published": "true",
        "raw_payload_json": json.dumps({"source": "docs/data-requests/20260806-data-request-casamento-garapha.md"}),
        "first_seen_at": now,
        "last_seen_at": now,
        "inserted_at": now,
        "row_updated_at": now,
        "service_agreement_url": TRIP["service_agreement_url"],
    }


def build_sheet_rows(seeded: list[dict[str, Any]]) -> dict[str, list[list[Any]]]:
    return {
        "Viagens": [[
            TRIP_UUID,
            TRIP["title"],
            TRIP["start_date"],
            TRIP["end_date"],
            TRIP["service_agreement_url"],
        ]],
        AUDIT_TAB: [
            [
                TRIP_UUID,
                traveler["full_name"],
                traveler["preferred_name"],
                traveler["phone"],
                traveler["email"],
                "Wedding Guest",
                "",
                "",
                "none",
                traveler.get("user_id", ""),
                traveler.get("trip_traveler_id", ""),
                "",
                "",
            ]
            for traveler in seeded
        ],
    }


def row_matches_trip_uuid(row: list[Any], header: list[str]) -> bool:
    normalized_header = [str(value).strip().lower() for value in header]
    try:
        trip_uuid_index = normalized_header.index("trip_uuid")
    except ValueError:
        return False
    return trip_uuid_index < len(row) and str(row[trip_uuid_index]).strip() == TRIP_UUID


def normalize_sheet_values(rows: list[list[Any]]) -> list[list[Any]]:
    return [["" if value is None else value for value in row] for row in rows]


async def table_exists(conn: asyncpg.Connection, table_name: str) -> bool:
    return bool(
        await conn.fetchval(
            """
            select exists (
              select 1 from information_schema.tables
              where table_schema='public' and table_name=$1
            )
            """,
            table_name,
        )
    )


async def upsert_trip(conn: asyncpg.Connection, now: datetime) -> None:
    trip = build_wetravel_trip_record(now)
    await conn.execute(
        """
        insert into wetravel_trips (
          id, entity_key, event_type, event_received_at, trip_uuid, trip_id,
          title, destination, currency, url, listing_status, start_date, end_date,
          published, raw_payload_json, first_seen_at, last_seen_at, inserted_at,
          row_updated_at, service_agreement_url
        )
        values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15::jsonb,$16,$17,$18,$19,$20)
        on conflict (entity_key) do update
        set title=excluded.title,
            destination=excluded.destination,
            currency=excluded.currency,
            start_date=excluded.start_date,
            end_date=excluded.end_date,
            url=excluded.url,
            listing_status=excluded.listing_status,
            published=excluded.published,
            raw_payload_json=excluded.raw_payload_json,
            last_seen_at=excluded.last_seen_at,
            row_updated_at=excluded.row_updated_at,
            service_agreement_url=excluded.service_agreement_url,
            trip_uuid=excluded.trip_uuid,
            trip_id=excluded.trip_id
        """,
        trip["id"],
        trip["entity_key"],
        trip["event_type"],
        trip["event_received_at"],
        trip["trip_uuid"],
        trip["trip_id"],
        trip["title"],
        trip["destination"],
        trip["currency"],
        trip["url"],
        trip["listing_status"],
        trip["start_date"],
        trip["end_date"],
        trip["published"],
        trip["raw_payload_json"],
        trip["first_seen_at"],
        trip["last_seen_at"],
        trip["inserted_at"],
        trip["row_updated_at"],
        trip["service_agreement_url"],
    )
    await conn.execute(
        """
        insert into trip_settings (id, trip_uuid, mode, ideal_pace_phase_id, created_at, updated_at)
        values ($1,$2,'pre-trip',null,$3,$3)
        on conflict (trip_uuid) do update
        set mode='pre-trip', updated_at=excluded.updated_at
        """,
        uuid.uuid4(),
        TRIP_UUID,
        now,
    )


async def upsert_travelers(conn: asyncpg.Connection, now: datetime) -> list[dict[str, Any]]:
    seeded: list[dict[str, Any]] = []
    has_products = await table_exists(conn, "traveler_products")
    for traveler in TRAVELERS:
        user_id = await conn.fetchval(
            """
            insert into users (id, phone, full_name, email, status, role, created_at, updated_at)
            values ($1,$2,$3,$4,'active','traveler',$5,$5)
            on conflict (phone) do update
            set full_name=excluded.full_name,
                email=excluded.email,
                status='active',
                role='traveler',
                updated_at=excluded.updated_at
            returning id
            """,
            uuid.uuid4(),
            traveler["phone"],
            traveler["full_name"],
            traveler["email"] or None,
            now,
        )
        trip_traveler_id = await conn.fetchval(
            """
            insert into trip_travelers (id, wetravel_trip_uuid, user_id, created_at, updated_at)
            values ($1,$2,$3,$4,$4)
            on conflict (wetravel_trip_uuid, user_id) do update
            set updated_at=excluded.updated_at
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
            values ($1,$2,$3,false,false,false,$4,$5,$5)
            on conflict (trip_traveler_id) do update
            set preferred_name=excluded.preferred_name,
                plus_one_flag=excluded.plus_one_flag,
                needs_flight_help_flag=excluded.needs_flight_help_flag,
                needs_travel_insurance_help_flag=excluded.needs_travel_insurance_help_flag,
                unforgettable_trip_details=excluded.unforgettable_trip_details,
                updated_at=excluded.updated_at
            """,
            uuid.uuid4(),
            trip_traveler_id,
            traveler["preferred_name"],
            "Casamento Gabriela e Raphael - noivos cadastrados como viajantes.",
            now,
        )
        if has_products:
            await conn.execute(
                """
                insert into traveler_products (id, trip_traveler_id, room_type, created_at, updated_at)
                values ($1,$2,'Wedding Guest',$3,$3)
                on conflict (trip_traveler_id) do update
                set room_type=excluded.room_type, updated_at=excluded.updated_at
                """,
                uuid.uuid4(),
                trip_traveler_id,
                now,
            )
        seeded.append({
            **traveler,
            "user_id": str(user_id),
            "trip_traveler_id": str(trip_traveler_id),
        })
    return seeded


async def discover(conn: asyncpg.Connection) -> dict[str, Any]:
    trip = await conn.fetchrow(
        "select trip_uuid,title,destination,start_date,end_date,url from wetravel_trips where trip_uuid=$1",
        TRIP_UUID,
    )
    travelers = await conn.fetch(
        """
        select u.phone,u.full_name,u.email,tt.id as trip_traveler_id,u.id as user_id
        from trip_travelers tt
        join users u on u.id=tt.user_id
        where tt.wetravel_trip_uuid=$1
        order by u.full_name
        """,
        TRIP_UUID,
    )
    return {
        "trip": dict(trip) if trip else None,
        "travelers": [dict(row) for row in travelers],
    }


def build_sheets_client():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds: Credentials | None = None
    if OAUTH_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not OAUTH_CLIENT_FILE.exists():
                raise RuntimeError(f"OAuth client file not found: {OAUTH_CLIENT_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        OAUTH_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("sheets", "v4", credentials=creds)


def replace_trip_rows(sheets: Any, spreadsheet_id: str, tab: str, new_rows: list[list[Any]]) -> None:
    header = CONTENT_TABS[tab]
    existing = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"'{tab}'!A:Z")
        .execute()
        .get("values", [])
    )
    existing_header = existing[0] if existing else header
    body = existing[1:] if existing else []
    kept = [row for row in body if not row_matches_trip_uuid(row, existing_header)]
    merged = normalize_sheet_values([existing_header] + kept + new_rows)
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


def update_sheets(rows: dict[str, list[list[Any]]]) -> dict[str, Any]:
    load_dotenv(BACKEND_ROOT / ".env")
    spreadsheet_id = os.environ.get("TRIP_CONTENT_SHEET_ID", "")
    if not spreadsheet_id:
        raise RuntimeError("TRIP_CONTENT_SHEET_ID is not configured")
    sheets = build_sheets_client()
    for tab, tab_rows in rows.items():
        replace_trip_rows(sheets, spreadsheet_id, tab, tab_rows)
    return {"content_sheet_id": spreadsheet_id, "updated_tabs": sorted(rows)}


def write_audit(output_dir: Path, report: dict[str, Any], seeded: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "result.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    rows = build_sheet_rows(seeded).get(AUDIT_TAB, [])
    with (output_dir / "travelers.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CONTENT_TABS[AUDIT_TAB])
        writer.writerows(rows)


async def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_dir = Path(args.output_dir)
    if not args.execute:
        summary = build_dry_run_summary()
        write_audit(output_dir, {"mode": "dry-run", **summary}, [])
        print(json.dumps(summary, indent=2))
        return

    now = datetime.now(UTC)
    database_url = load_database_url()
    report: dict[str, Any] = {
        "mode": "execute",
        "trip_uuid": TRIP_UUID,
        "started_at": now.isoformat(),
        "sheets": None,
    }
    conn = await asyncpg.connect(database_url)
    try:
        report["before"] = await discover(conn)
        async with conn.transaction():
            await upsert_trip(conn, now)
            seeded = await upsert_travelers(conn, now)
        rows = build_sheet_rows(seeded)
        if not args.skip_sheets:
            report["sheets"] = update_sheets(rows)
        report["after"] = await discover(conn)
        report["seeded_travelers"] = seeded
        write_audit(output_dir, report, seeded)
        print(json.dumps({"seeded": len(seeded), "sheets_updated": not args.skip_sheets}, indent=2))
    finally:
        await conn.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

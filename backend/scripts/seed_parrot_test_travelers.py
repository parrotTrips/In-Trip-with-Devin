"""Seed 20 fictitious travelers for TEST-2026-FULL and generate QR PNGs.

This script writes to real Supabase/Google Sheets/Google Drive only with
--execute. The default --dry-run prints what would be changed.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import asyncpg
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.qr_service import create_traveler_qr_payload


TRIP_UUID = "TEST-2026-FULL"
TRIP_TITLE = "Viagem Interna Parrot"
TRIP_CONTENT_SHEET_ID = "1N1B66s1-K4DDf2_863frmhnpF6LRZB_ww60uax0gKZM"
STAFF_CONTENT_SHEET_ID = "1iVv9k45F3dacjYEwR4TsIuGuFtFmVgN3y0ueghvNWiI"
QR_DRIVE_FOLDER_ID = "1qXJejeBsUBw7st3ipwJtpppcbwZLXZsE"
OUTPUT_DIR = Path("outputs/parrot-test-travelers")
AUDIT_TAB = "Viajantes Teste"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
OAUTH_TOKEN_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-token.json"
OAUTH_CLIENT_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-credentials.json"


def _profile(
    preferred_name: str,
    passport_number: str,
    dietary: bool,
    dietary_details: str | None,
    seasick: bool,
) -> dict[str, Any]:
    return {
        "preferred_name": preferred_name,
        "date_of_birth": "1994-04-12",
        "gender": "Test",
        "passport_first_name": preferred_name,
        "passport_last_name": "Test",
        "passport_country": "USA",
        "passport_number": passport_number,
        "passport_issue_date": "2022-01-15",
        "passport_expiration_date": "2032-01-14",
        "dietary_restrictions_flag": dietary,
        "dietary_restrictions_details": dietary_details,
        "seasickness_flag": seasick,
        "plus_one_flag": False,
        "plus_one_name": None,
        "plus_one_email": None,
        "needs_flight_help_flag": False,
        "flight_help_details": None,
        "needs_travel_insurance_help_flag": True,
        "unforgettable_trip_details": "Fictitious traveler for Parrot internal QR testing.",
        "avatar_url": None,
    }


TEST_TRAVELERS: list[dict[str, Any]] = [
    {
        "index": 1,
        "full_name": "Lara Mendes",
        "preferred_name": "Lara",
        "phone": "+15550102001",
        "email": "lara.mendes@example.com",
        "package_name": "Rio Test Package - Single Room",
        "room_type": "Single Room",
        "paid_amount_usd": 1250,
        "addons": ["Sunset Boat Add-on"],
        "profile": _profile("Lara", "PTEST001", False, None, False),
    },
    {
        "index": 2,
        "full_name": "Noah Carter",
        "preferred_name": "Noah",
        "phone": "+15550102002",
        "email": "noah.carter@example.com",
        "package_name": "Rio Test Package - Double Room",
        "room_type": "Double Room",
        "paid_amount_usd": 2200,
        "addons": ["Samba Night"],
        "profile": _profile("Noah", "PTEST002", True, "Vegetarian", False),
    },
    {
        "index": 3,
        "full_name": "Maya Brooks",
        "preferred_name": "Maya",
        "phone": "+15550102003",
        "email": "maya.brooks@example.com",
        "package_name": "Rio Test Package - Twin Shared Room",
        "room_type": "Twin Shared Room",
        "paid_amount_usd": 1100,
        "addons": ["Staff Shadow Add-on"],
        "profile": _profile("Maya", "PTEST003", False, None, True),
    },
    {
        "index": 4,
        "full_name": "Ethan Silva",
        "preferred_name": "Ethan",
        "phone": "+15550102004",
        "email": "ethan.silva@example.com",
        "package_name": "Rio Test Package - Single Room",
        "room_type": "Single Room",
        "paid_amount_usd": 1250,
        "addons": ["Airport Fast Track"],
        "profile": _profile("Ethan", "PTEST004", False, None, False),
    },
    {
        "index": 5,
        "full_name": "Sofia Grant",
        "preferred_name": "Sofia",
        "phone": "+15550102005",
        "email": "sofia.grant@example.com",
        "package_name": "Rio Test Package - Double Room",
        "room_type": "Double Room",
        "paid_amount_usd": 2200,
        "addons": ["Sunset Boat Add-on", "Samba Night"],
        "profile": _profile("Sofia", "PTEST005", True, "No shellfish", False),
    },
    {
        "index": 6,
        "full_name": "Lucas Bennett",
        "preferred_name": "Lucas",
        "phone": "+15550102006",
        "email": "lucas.bennett@example.com",
        "package_name": "Rio Test Package - Twin Shared Room",
        "room_type": "Twin Shared Room",
        "paid_amount_usd": 1100,
        "addons": [],
        "profile": _profile("Lucas", "PTEST006", False, None, True),
    },
    {
        "index": 7,
        "full_name": "Emma Torres",
        "preferred_name": "Emma",
        "phone": "+15550102007",
        "email": "emma.torres@example.com",
        "package_name": "Rio Test Package - Single Room",
        "room_type": "Single Room",
        "paid_amount_usd": 1250,
        "addons": ["Local Food Add-on"],
        "profile": _profile("Emma", "PTEST007", True, "Gluten free", False),
    },
    {
        "index": 8,
        "full_name": "Owen Price",
        "preferred_name": "Owen",
        "phone": "+15550102008",
        "email": "owen.price@example.com",
        "package_name": "Rio Test Package - Double Room",
        "room_type": "Double Room",
        "paid_amount_usd": 2200,
        "addons": ["Boat Add-on"],
        "profile": _profile("Owen", "PTEST008", False, None, False),
    },
    {
        "index": 9,
        "full_name": "Ava Stone",
        "preferred_name": "Ava",
        "phone": "+15550102009",
        "email": "ava.stone@example.com",
        "package_name": "Rio Test Package - Twin Shared Room",
        "room_type": "Twin Shared Room",
        "paid_amount_usd": 1100,
        "addons": ["QR Ops Add-on"],
        "profile": _profile("Ava", "PTEST009", False, None, True),
    },
    {
        "index": 10,
        "full_name": "Mateo Reed",
        "preferred_name": "Mateo",
        "phone": "+15550102010",
        "email": "mateo.reed@example.com",
        "package_name": "Rio Test Package - Single Room",
        "room_type": "Single Room",
        "paid_amount_usd": 1250,
        "addons": ["Sunset Boat Add-on"],
        "profile": _profile("Mateo", "PTEST010", True, "Dairy free", False),
    },
    {
        "index": 11,
        "full_name": "Chloe Fisher",
        "preferred_name": "Chloe",
        "phone": "+15550102011",
        "email": "chloe.fisher@example.com",
        "package_name": "Rio Test Package - Double Room",
        "room_type": "Double Room",
        "paid_amount_usd": 2200,
        "addons": ["Samba Night"],
        "profile": _profile("Chloe", "PTEST011", False, None, False),
    },
    {
        "index": 12,
        "full_name": "Daniel Park",
        "preferred_name": "Daniel",
        "phone": "+15550102012",
        "email": "daniel.park@example.com",
        "package_name": "Rio Test Package - Twin Shared Room",
        "room_type": "Twin Shared Room",
        "paid_amount_usd": 1100,
        "addons": ["Airport Fast Track"],
        "profile": _profile("Daniel", "PTEST012", False, None, True),
    },
    {
        "index": 13,
        "full_name": "Nina Hughes",
        "preferred_name": "Nina",
        "phone": "+15550102013",
        "email": "nina.hughes@example.com",
        "package_name": "Rio Test Package - Single Room",
        "room_type": "Single Room",
        "paid_amount_usd": 1250,
        "addons": ["Local Food Add-on"],
        "profile": _profile("Nina", "PTEST013", True, "Vegan", False),
    },
    {
        "index": 14,
        "full_name": "Leo Martin",
        "preferred_name": "Leo",
        "phone": "+15550102014",
        "email": "leo.martin@example.com",
        "package_name": "Rio Test Package - Double Room",
        "room_type": "Double Room",
        "paid_amount_usd": 2200,
        "addons": [],
        "profile": _profile("Leo", "PTEST014", False, None, False),
    },
    {
        "index": 15,
        "full_name": "Isla Morgan",
        "preferred_name": "Isla",
        "phone": "+15550102015",
        "email": "isla.morgan@example.com",
        "package_name": "Rio Test Package - Twin Shared Room",
        "room_type": "Twin Shared Room",
        "paid_amount_usd": 1100,
        "addons": ["Boat Add-on"],
        "profile": _profile("Isla", "PTEST015", False, None, True),
    },
    {
        "index": 16,
        "full_name": "Julian King",
        "preferred_name": "Julian",
        "phone": "+15550102016",
        "email": "julian.king@example.com",
        "package_name": "Rio Test Package - Single Room",
        "room_type": "Single Room",
        "paid_amount_usd": 1250,
        "addons": ["QR Ops Add-on"],
        "profile": _profile("Julian", "PTEST016", False, None, False),
    },
    {
        "index": 17,
        "full_name": "Mila Scott",
        "preferred_name": "Mila",
        "phone": "+15550102017",
        "email": "mila.scott@example.com",
        "package_name": "Rio Test Package - Double Room",
        "room_type": "Double Room",
        "paid_amount_usd": 2200,
        "addons": ["Sunset Boat Add-on", "Local Food Add-on"],
        "profile": _profile("Mila", "PTEST017", True, "Peanut allergy", False),
    },
    {
        "index": 18,
        "full_name": "Ryan Cooper",
        "preferred_name": "Ryan",
        "phone": "+15550102018",
        "email": "ryan.cooper@example.com",
        "package_name": "Rio Test Package - Twin Shared Room",
        "room_type": "Twin Shared Room",
        "paid_amount_usd": 1100,
        "addons": ["Staff Shadow Add-on"],
        "profile": _profile("Ryan", "PTEST018", False, None, True),
    },
    {
        "index": 19,
        "full_name": "Zoe Rivera",
        "preferred_name": "Zoe",
        "phone": "+15550102019",
        "email": "zoe.rivera@example.com",
        "package_name": "Rio Test Package - Single Room",
        "room_type": "Single Room",
        "paid_amount_usd": 1250,
        "addons": ["Samba Night"],
        "profile": _profile("Zoe", "PTEST019", False, None, False),
    },
    {
        "index": 20,
        "full_name": "Theo Wallace",
        "preferred_name": "Theo",
        "phone": "+15550102020",
        "email": "theo.wallace@example.com",
        "package_name": "Rio Test Package - Double Room",
        "room_type": "Double Room",
        "paid_amount_usd": 2200,
        "addons": ["Boat Add-on"],
        "profile": _profile("Theo", "PTEST020", True, "No red meat", False),
    },
]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def qr_filename(traveler: dict[str, Any]) -> str:
    return f"parrot-test-{traveler['index']:02d}-{slugify(traveler['full_name'])}.png"


def build_restricted_activity_allowlists(travelers: list[dict[str, Any]]) -> dict[str, list[str]]:
    phones = [traveler["phone"] for traveler in travelers]
    return {
        "Internal Parrot Ops Briefing": phones[:8],
        "Sugarloaf Sunset Test": phones[:12],
        "Restricted Boat Boarding": phones[::3][:7],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Parrot fictitious travelers and QR codes.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--execute", action="store_true")
    parser.add_argument("--skip-sheets", action="store_true")
    parser.add_argument("--skip-drive", action="store_true")
    parser.add_argument("--use-oauth", action="store_true", help="Use local OAuth user credentials instead of the service account.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args(argv)


def load_env() -> str:
    load_dotenv(Path(__file__).parent.parent / ".env")
    database_url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg", "postgresql")
    if not os.environ.get("JWT_SECRET"):
        raise RuntimeError("JWT_SECRET is required to generate QR payloads")
    return database_url


def get_google_services(use_oauth: bool = False):
    if use_oauth:
        credentials = get_oauth_credentials()
        return build("sheets", "v4", credentials=credentials), build("drive", "v3", credentials=credentials)
    key = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "secrets/gcp-service-account.json")
    credentials = service_account.Credentials.from_service_account_file(
        Path(__file__).parent.parent / key,
        scopes=GOOGLE_SCOPES,
    )
    return build("sheets", "v4", credentials=credentials), build("drive", "v3", credentials=credentials)


def get_oauth_credentials() -> Credentials:
    credentials: Credentials | None = None
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
    return credentials


def cents(amount_usd: int | float | Decimal) -> int:
    return int(Decimal(str(amount_usd)) * 100)


def order_id(traveler: dict[str, Any]) -> str:
    return f"PARROT-TEST-ORDER-{traveler['index']:02d}"


def participant_id(traveler: dict[str, Any]) -> str:
    return f"PARROT-TEST-PARTICIPANT-{traveler['index']:02d}"


async def discover(conn: asyncpg.Connection) -> dict[str, Any]:
    phones = [traveler["phone"] for traveler in TEST_TRAVELERS]
    trip = await conn.fetchrow(
        "select trip_uuid,title,destination,start_date,end_date from wetravel_trips where trip_uuid=$1",
        TRIP_UUID,
    )
    existing_users = await conn.fetch(
        "select id,phone,full_name,email,role from users where phone = any($1::text[]) order by phone",
        phones,
    )
    linked = await conn.fetch(
        """
        select tt.id,u.phone,u.full_name
        from trip_travelers tt
        join users u on u.id=tt.user_id
        where tt.wetravel_trip_uuid=$1 and u.phone = any($2::text[])
        order by u.phone
        """,
        TRIP_UUID,
        phones,
    )
    return {
        "trip": dict(trip) if trip else None,
        "existing_test_users": [dict(row) for row in existing_users],
        "existing_test_trip_links": [dict(row) for row in linked],
        "traveler_count": len(TEST_TRAVELERS),
    }


async def upsert_travelers(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    seeded: list[dict[str, Any]] = []
    for traveler in TEST_TRAVELERS:
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
            traveler["email"],
            now,
        )
        trip_traveler_id = await conn.fetchval(
            """
            insert into trip_travelers (id,wetravel_trip_uuid,user_id,created_at,updated_at)
            values ($1,$2,$3,$4,$4)
            on conflict (wetravel_trip_uuid,user_id) do update
            set updated_at=excluded.updated_at
            returning id
            """,
            uuid.uuid4(),
            TRIP_UUID,
            user_id,
            now,
        )
        profile = traveler["profile"]
        await conn.execute(
            """
            insert into traveler_profiles (
              id, trip_traveler_id, preferred_name, date_of_birth, gender,
              passport_first_name, passport_last_name, passport_country, passport_number,
              passport_issue_date, passport_expiration_date, dietary_restrictions_flag,
              dietary_restrictions_details, seasickness_flag, plus_one_flag, plus_one_name,
              plus_one_email, needs_flight_help_flag, flight_help_details,
              needs_travel_insurance_help_flag, unforgettable_trip_details, avatar_url,
              created_at, updated_at
            )
            values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$23)
            on conflict (trip_traveler_id) do update
            set preferred_name=excluded.preferred_name,
                date_of_birth=excluded.date_of_birth,
                gender=excluded.gender,
                passport_first_name=excluded.passport_first_name,
                passport_last_name=excluded.passport_last_name,
                passport_country=excluded.passport_country,
                passport_number=excluded.passport_number,
                passport_issue_date=excluded.passport_issue_date,
                passport_expiration_date=excluded.passport_expiration_date,
                dietary_restrictions_flag=excluded.dietary_restrictions_flag,
                dietary_restrictions_details=excluded.dietary_restrictions_details,
                seasickness_flag=excluded.seasickness_flag,
                plus_one_flag=excluded.plus_one_flag,
                plus_one_name=excluded.plus_one_name,
                plus_one_email=excluded.plus_one_email,
                needs_flight_help_flag=excluded.needs_flight_help_flag,
                flight_help_details=excluded.flight_help_details,
                needs_travel_insurance_help_flag=excluded.needs_travel_insurance_help_flag,
                unforgettable_trip_details=excluded.unforgettable_trip_details,
                avatar_url=excluded.avatar_url,
                updated_at=excluded.updated_at
            """,
            uuid.uuid4(),
            trip_traveler_id,
            profile["preferred_name"],
            date.fromisoformat(profile["date_of_birth"]),
            profile["gender"],
            profile["passport_first_name"],
            profile["passport_last_name"],
            profile["passport_country"],
            profile["passport_number"],
            date.fromisoformat(profile["passport_issue_date"]),
            date.fromisoformat(profile["passport_expiration_date"]),
            profile["dietary_restrictions_flag"],
            profile["dietary_restrictions_details"],
            profile["seasickness_flag"],
            profile["plus_one_flag"],
            profile["plus_one_name"],
            profile["plus_one_email"],
            profile["needs_flight_help_flag"],
            profile["flight_help_details"],
            profile["needs_travel_insurance_help_flag"],
            profile["unforgettable_trip_details"],
            profile["avatar_url"],
            now,
        )
        await conn.execute(
            """
            insert into traveler_products (id,trip_traveler_id,room_type,created_at,updated_at)
            values ($1,$2,$3,$4,$4)
            on conflict (trip_traveler_id) do update
            set room_type=excluded.room_type, updated_at=excluded.updated_at
            """,
            uuid.uuid4(),
            trip_traveler_id,
            traveler["room_type"],
            now,
        )
        await upsert_wetravel_like_rows(conn, traveler, now)
        seeded.append({**traveler, "user_id": str(user_id), "trip_traveler_id": str(trip_traveler_id)})
    await replace_activity_allowlists(conn, seeded, now)
    return seeded


async def upsert_wetravel_like_rows(conn: asyncpg.Connection, traveler: dict[str, Any], now: datetime) -> None:
    oid = order_id(traveler)
    pid = participant_id(traveler)
    participant = {
        "id": pid,
        "full_name": traveler["full_name"],
        "email": traveler["email"],
        "cancelled": False,
    }
    participants_json = json.dumps([participant])
    paid = cents(traveler["paid_amount_usd"])
    await conn.execute(
        """
        insert into wetravel_bookings (
          id, entity_key, order_id, trip_uuid, trip_title, trip_currency,
          buyer_email, buyer_full_name, booking_event_type,
          total_deposit_amount, total_due_amount, total_paid_amount, total_price_amount,
          participant_count, cancelled_participant_count, participants_json,
          first_seen_at, inserted_at, row_updated_at
        )
        values ($1,$2,$3,$4,$5,'USD',$6,$7,'booking_confirmed',$8,0,$8,$8,1,0,$9,$10,$10,$10)
        on conflict (entity_key) do update
        set buyer_email=excluded.buyer_email,
            buyer_full_name=excluded.buyer_full_name,
            total_paid_amount=excluded.total_paid_amount,
            total_price_amount=excluded.total_price_amount,
            participants_json=excluded.participants_json,
            row_updated_at=excluded.row_updated_at
        """,
        uuid.uuid4(),
        f"booking:{oid}",
        oid,
        TRIP_UUID,
        TRIP_TITLE,
        traveler["email"],
        traveler["full_name"],
        paid,
        participants_json,
        now,
    )
    await conn.execute(
        """
        insert into wetravel_payments (
          id, entity_key, payment_id, order_id, trip_uuid, trip_title,
          buyer_email, buyer_full_name, status, payment_method, payment_type,
          currency, storage_currency, subtotal_amount, total_amount, net_amount,
          payment_processing_fee, refunded_amount, disputed_amount, participant_count,
          participants_json, first_seen_at, inserted_at, row_updated_at
        )
        values ($1,$2,$3,$4,$5,$6,$7,$8,'processed','test_card','full','USD','USD',$9,$9,$9,0,0,0,1,$10,$11,$11,$11)
        on conflict (entity_key) do update
        set total_amount=excluded.total_amount,
            subtotal_amount=excluded.subtotal_amount,
            participants_json=excluded.participants_json,
            row_updated_at=excluded.row_updated_at
        """,
        uuid.uuid4(),
        f"payment:{oid}",
        f"PARROT-TEST-PAYMENT-{traveler['index']:02d}",
        oid,
        TRIP_UUID,
        TRIP_TITLE,
        traveler["email"],
        traveler["full_name"],
        paid,
        participants_json,
        now,
    )
    options = [("package", traveler["package_name"], paid, f"PKG-{traveler['index']:02d}")]
    addon_price = 0
    for addon_index, addon in enumerate(traveler["addons"], start=1):
        options.append(("option", addon, addon_price, f"ADDON-{traveler['index']:02d}-{addon_index:02d}"))
    for option_type, option_name, price, option_id in options:
        await conn.execute(
            """
            insert into wetravel_order_options (
              id, order_id, trip_uuid, option_id, option_type, option_name,
              active_count, cancelled_count, price, deposit_amount,
              participants_json, source, synced_at, row_updated_at
            )
            values ($1,$2,$3,$4,$5,$6,1,0,$7,0,$8,'parrot-test-seed',$9,$9)
            on conflict (order_id, option_id) do update
            set option_type=excluded.option_type,
                option_name=excluded.option_name,
                price=excluded.price,
                participants_json=excluded.participants_json,
                row_updated_at=excluded.row_updated_at
            """,
            uuid.uuid4(),
            oid,
            TRIP_UUID,
            option_id,
            option_type,
            option_name,
            price,
            participants_json,
            now,
        )
    await conn.execute(
        """
        insert into wetravel_participant_phones (participant_id,email,phone,full_name,trip_uuid,order_id,synced_at,row_updated_at)
        values ($1,$2,$3,$4,$5,$6,$7,$7)
        on conflict (participant_id) do update
        set email=excluded.email,
            phone=excluded.phone,
            full_name=excluded.full_name,
            trip_uuid=excluded.trip_uuid,
            order_id=excluded.order_id,
            row_updated_at=excluded.row_updated_at
        """,
        pid,
        traveler["email"],
        traveler["phone"],
        traveler["full_name"],
        TRIP_UUID,
        oid,
        now,
    )


async def replace_activity_allowlists(conn: asyncpg.Connection, seeded: list[dict[str, Any]], now: datetime) -> None:
    allowlists = build_restricted_activity_allowlists(TEST_TRAVELERS)
    phone_to_ttid = {traveler["phone"]: traveler["trip_traveler_id"] for traveler in seeded}
    activity_rows = await conn.fetch(
        """
        select a.id,a.name
        from trip_activities a
        join trip_phases p on p.id=a.trip_phase_id
        where p.wetravel_trip_uuid=$1 and a.name = any($2::text[])
        """,
        TRIP_UUID,
        list(allowlists),
    )
    activity_by_name = {row["name"]: row["id"] for row in activity_rows}
    if set(activity_by_name) != set(allowlists):
        missing = sorted(set(allowlists) - set(activity_by_name))
        raise RuntimeError(f"Missing restricted activities: {missing}")
    await conn.execute(
        "delete from activity_participants where trip_activity_id = any($1::uuid[])",
        list(activity_by_name.values()),
    )
    for activity_name, phones in allowlists.items():
        for phone in phones:
            await conn.execute(
                """
                insert into activity_participants (id,trip_activity_id,trip_traveler_id,status,created_at,updated_at)
                values ($1,$2,$3,'allowed',$4,$4)
                on conflict (trip_activity_id,trip_traveler_id) do update
                set status='allowed', updated_at=excluded.updated_at
                """,
                uuid.uuid4(),
                activity_by_name[activity_name],
                uuid.UUID(phone_to_ttid[phone]),
                now,
            )


async def fetch_sheet_payload(conn: asyncpg.Connection, seeded: list[dict[str, Any]], qr_records: list[dict[str, str]]) -> dict[str, Any]:
    trip = await conn.fetchrow(
        "select trip_uuid,title,start_date,end_date,destination from wetravel_trips where trip_uuid=$1",
        TRIP_UUID,
    )
    phases = await conn.fetch(
        """
        select id,phase_type,title,subtitle,icon,short_description,detailed_description,sort_order,starts_at
        from trip_phases where wetravel_trip_uuid=$1 order by sort_order
        """,
        TRIP_UUID,
    )
    phase_ids = [row["id"] for row in phases]
    checklist = await conn.fetch(
        """
        select p.title phase_title,p.sort_order phase_order,i.sort_order,i.label,i.is_required
        from trip_phase_checklist_items i
        join trip_phases p on p.id=i.trip_phase_id
        where p.wetravel_trip_uuid=$1
        order by p.sort_order,i.sort_order
        """,
        TRIP_UUID,
    )
    links = await conn.fetch(
        """
        select p.title phase_title,p.sort_order phase_order,l.sort_order,l.label,l.url
        from trip_phase_links l
        join trip_phases p on p.id=l.trip_phase_id
        where p.wetravel_trip_uuid=$1
        order by p.sort_order,l.sort_order
        """,
        TRIP_UUID,
    )
    activities = await conn.fetch(
        """
        select p.sort_order phase_order,p.title phase_title,p.subtitle phase_subtitle,p.icon phase_icon,
               p.short_description phase_short_description,p.detailed_description phase_detailed_description,
               p.starts_at phase_starts_at,a.name,a.activity_type,a.starts_at,a.duration_minutes,
               a.short_description,a.practical_info,a.amount_brl,a.sort_order,a.address,a.max_checkins
        from trip_activities a
        join trip_phases p on p.id=a.trip_phase_id
        where p.wetravel_trip_uuid=$1
        order by p.sort_order,a.sort_order
        """,
        TRIP_UUID,
    )
    emergency = await conn.fetch(
        "select name,role,phone,sort_order from trip_emergency_contacts where wetravel_trip_uuid=$1 order by sort_order",
        TRIP_UUID,
    )
    recommendations = await conn.fetch(
        """
        select name,description,address,photo_url,sort_order,category,neighborhood,location,highlight,price_range,rating,map_url,emoji
        from trip_recommendations where wetravel_trip_uuid=$1 order by sort_order
        """,
        TRIP_UUID,
    )
    contacts = await conn.fetch(
        "select category,name,role,phone,sort_order from trip_contacts where wetravel_trip_uuid=$1 order by category,sort_order",
        TRIP_UUID,
    )
    staff = await conn.fetch(
        """
        select u.phone,u.full_name,ts.function,ts.photo_url,ts.bio
        from trip_staff ts join users u on u.id=ts.user_id
        where ts.wetravel_trip_uuid=$1
        order by u.full_name
        """,
        TRIP_UUID,
    )
    tasks = await conn.fetch(
        """
        select p.sort_order phase_order,ta.name activity_name,u.phone staff_phone,st.title,st.description,st.sort_order
        from staff_tasks st
        left join trip_activities ta on ta.id=st.trip_activity_id
        left join trip_phases p on p.id=coalesce(ta.trip_phase_id, st.trip_phase_id)
        left join users u on u.id=st.assigned_to_user_id
        where p.wetravel_trip_uuid=$1
        order by p.sort_order,ta.name,st.sort_order
        """,
        TRIP_UUID,
    )
    participants = await conn.fetch(
        """
        select p.sort_order phase_order,a.name activity_name,u.phone,ap.status
        from activity_participants ap
        join trip_activities a on a.id=ap.trip_activity_id
        join trip_phases p on p.id=a.trip_phase_id
        join trip_travelers tt on tt.id=ap.trip_traveler_id
        join users u on u.id=tt.user_id
        where p.wetravel_trip_uuid=$1
        order by p.sort_order,a.sort_order,u.full_name
        """,
        TRIP_UUID,
    )
    qr_by_phone = {record["phone"]: record for record in qr_records}
    traveler_rows = []
    for traveler in seeded:
        qr = qr_by_phone.get(traveler["phone"], {})
        traveler_rows.append(
            [
                TRIP_UUID,
                traveler["full_name"],
                traveler["preferred_name"],
                traveler["phone"],
                traveler["email"],
                traveler["package_name"],
                traveler["room_type"],
                str(traveler["paid_amount_usd"]),
                ", ".join(traveler["addons"]) or "none",
                traveler["user_id"],
                traveler["trip_traveler_id"],
                qr_filename(traveler),
                qr.get("drive_web_view_link", ""),
            ]
        )
    return {
        "trip": dict(trip),
        "phases": [dict(row) for row in phases],
        "phase_ids": phase_ids,
        "checklist": [dict(row) for row in checklist],
        "links": [dict(row) for row in links],
        "activities": [dict(row) for row in activities],
        "emergency": [dict(row) for row in emergency],
        "recommendations": [dict(row) for row in recommendations],
        "contacts": [dict(row) for row in contacts],
        "staff": [dict(row) for row in staff],
        "tasks": [dict(row) for row in tasks],
        "participants": [dict(row) for row in participants],
        "traveler_rows": traveler_rows,
    }


def iso_date(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value[:10]
    return value.isoformat()[:10]


def local_time(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value[11:16]
    return value.astimezone().strftime("%H:%M")


def phase_key(row: dict[str, Any]) -> str:
    return slugify(row["title"]).replace("-", "_")


def build_sheet_rows(payload: dict[str, Any]) -> dict[str, dict[str, list[list[Any]]]]:
    trip = payload["trip"]
    pretrip = [row for row in payload["phases"] if row["phase_type"] == "pre-trip"]
    in_trip = [row for row in payload["phases"] if row["phase_type"] == "in-trip"]
    phase_order_to_key = {row["sort_order"]: phase_key(row) for row in payload["phases"]}
    content_rows = {
        "Viagens": [[TRIP_UUID, TRIP_TITLE, iso_date(trip["start_date"]), iso_date(trip["end_date"]), ""]],
        "Emergency Contacts": [
            [TRIP_UUID, row["name"], row["role"], row["phone"], row["sort_order"]]
            for row in payload["emergency"]
        ],
        "Recomendacoes": [
            [
                TRIP_UUID,
                row["name"],
                row["description"],
                row["address"],
                row.get("photo_url") or "",
                row["sort_order"],
                row["category"],
                row["neighborhood"],
                row["location"],
                row["highlight"],
                row["price_range"],
                str(row["rating"] or ""),
                row.get("map_url") or "",
                row.get("emoji") or "",
            ]
            for row in payload["recommendations"]
        ],
        "Fases": [
            [
                TRIP_UUID,
                row["sort_order"] + 1,
                phase_key(row),
                row["title"],
                row.get("subtitle") or "",
                row.get("icon") or "",
                row["short_description"],
                row.get("detailed_description") or "",
                "true" if phase_key(row) == "operational_checklist" else "",
            ]
            for row in pretrip
        ],
        "Checklist": [
            [
                TRIP_UUID,
                phase_order_to_key[row["phase_order"]],
                row["sort_order"] + 1,
                row["label"],
                "true" if row["is_required"] else "false",
            ]
            for row in payload["checklist"]
        ],
        "Links": [
            [TRIP_UUID, phase_order_to_key[row["phase_order"]], row["sort_order"] + 1, row["label"], row["url"]]
            for row in payload["links"]
        ],
        "Roteiro": [
            [
                TRIP_UUID,
                row["phase_order"] - min([p["sort_order"] for p in in_trip], default=0) + 1,
                iso_date(row["phase_starts_at"]),
                row["phase_title"],
                row.get("phase_subtitle") or "",
                row.get("phase_icon") or "",
                row["phase_short_description"],
                row.get("phase_detailed_description") or "",
                row["name"],
                row["activity_type"],
                local_time(row["starts_at"]),
                row["duration_minutes"] or "",
                row["short_description"],
                row.get("practical_info") or "",
                row.get("amount_brl") or "",
                row.get("address") or "",
                row["max_checkins"],
            ]
            for row in payload["activities"]
        ],
        AUDIT_TAB: payload["traveler_rows"],
    }
    staff_rows = {
        "Viagens": [[TRIP_UUID, TRIP_TITLE, iso_date(trip["start_date"]), iso_date(trip["end_date"])]],
        "Contatos": [
            [TRIP_UUID, row["category"], row["name"], row["role"] or "", row["phone"] or "", row["sort_order"]]
            for row in payload["contacts"]
        ],
        "Staff": [
            [row["phone"], row["full_name"], row["function"] or "", TRIP_UUID, row.get("photo_url") or "", row.get("bio") or ""]
            for row in payload["staff"]
        ],
        "Tarefas Staff": [
            [
                TRIP_UUID,
                row["phase_order"] or "",
                row["activity_name"] or "",
                row["staff_phone"] or "",
                row["title"],
                row["description"] or "",
                row["sort_order"],
            ]
            for row in payload["tasks"]
        ],
        "Participantes Atividades": [
            [TRIP_UUID, row["phase_order"], row["activity_name"], row["phone"], row["status"]]
            for row in payload["participants"]
        ],
        AUDIT_TAB: payload["traveler_rows"],
    }
    return {"content": content_rows, "staff": staff_rows}


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


def ensure_tab(sheets, spreadsheet_id: str, tab: str) -> None:
    meta = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title").execute()
    titles = {sheet["properties"]["title"] for sheet in meta["sheets"]}
    if tab in titles:
        return
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
    ).execute()


def replace_trip_rows(sheets, spreadsheet_id: str, tab: str, new_rows: list[list[Any]]) -> None:
    ensure_tab(sheets, spreadsheet_id, tab)
    values = sheets.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f"'{tab}'!A:Z").execute().get("values", [])
    if values:
        header = values[0]
        body = values[1:]
    else:
        header = AUDIT_HEADER if tab == AUDIT_TAB else []
        body = []
    if tab == AUDIT_TAB:
        header = AUDIT_HEADER
    kept = [row for row in body if not row or row[0] != TRIP_UUID]
    merged = normalize_sheet_values([header] + kept + new_rows)
    sheets.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=f"'{tab}'!A:Z").execute()
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{tab}'!A1",
        valueInputOption="RAW",
        body={"values": merged},
    ).execute()


def normalize_sheet_values(rows: list[list[Any]]) -> list[list[Any]]:
    normalized = []
    for row in rows:
        normalized_row = []
        for value in row:
            if value is None:
                normalized_row.append("")
            elif isinstance(value, Decimal):
                normalized_row.append(str(value))
            elif isinstance(value, (datetime, date)):
                normalized_row.append(value.isoformat())
            else:
                normalized_row.append(value)
        normalized.append(normalized_row)
    return normalized


def update_sheets(sheets, rows: dict[str, dict[str, list[list[Any]]]]) -> dict[str, Any]:
    for tab, tab_rows in rows["content"].items():
        replace_trip_rows(sheets, TRIP_CONTENT_SHEET_ID, tab, tab_rows)
    for tab, tab_rows in rows["staff"].items():
        replace_trip_rows(sheets, STAFF_CONTENT_SHEET_ID, tab, tab_rows)
    return {
        "content_sheet_id": TRIP_CONTENT_SHEET_ID,
        "staff_sheet_id": STAFF_CONTENT_SHEET_ID,
        "updated_tabs": {"content": sorted(rows["content"]), "staff": sorted(rows["staff"])},
    }


def render_qr_png(payload: str, path: Path) -> None:
    try:
        import qrcode
    except ImportError as exc:
        raise RuntimeError("Missing dependency: install qrcode[pil] to generate QR PNGs") from exc
    image = qrcode.make(payload)
    image.save(path)


def find_drive_file(drive, filename: str) -> str | None:
    escaped = filename.replace("'", "\\'")
    result = drive.files().list(
        q=f"'{QR_DRIVE_FOLDER_ID}' in parents and name = '{escaped}' and trashed = false",
        fields="files(id,name)",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()
    files = result.get("files", [])
    return files[0]["id"] if files else None


def generate_and_upload_qrs(drive, seeded: list[dict[str, Any]], output_dir: Path) -> list[dict[str, str]]:
    qr_dir = output_dir / "qr"
    qr_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, str]] = []
    for traveler in seeded:
        payload = create_traveler_qr_payload(traveler["trip_traveler_id"], TRIP_UUID)
        filename = qr_filename(traveler)
        local_path = qr_dir / filename
        render_qr_png(payload, local_path)
        existing_id = find_drive_file(drive, filename)
        media = MediaFileUpload(str(local_path), mimetype="image/png", resumable=False)
        if existing_id:
            file_meta = drive.files().update(
                fileId=existing_id,
                media_body=media,
                fields="id,name,webViewLink",
                supportsAllDrives=True,
            ).execute()
        else:
            file_meta = drive.files().create(
                body={"name": filename, "parents": [QR_DRIVE_FOLDER_ID]},
                media_body=media,
                fields="id,name,webViewLink",
                supportsAllDrives=True,
            ).execute()
        records.append(
            {
                "phone": traveler["phone"],
                "full_name": traveler["full_name"],
                "qr_filename": filename,
                "drive_file_id": file_meta["id"],
                "drive_web_view_link": file_meta.get("webViewLink", ""),
            }
        )
    return records


def write_audit(output_dir: Path, report: dict[str, Any], seeded: list[dict[str, Any]], qr_records: list[dict[str, str]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "result.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    qr_by_phone = {record["phone"]: record for record in qr_records}
    with (output_dir / "travelers.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_HEADER)
        writer.writeheader()
        for traveler in seeded:
            qr = qr_by_phone.get(traveler["phone"], {})
            writer.writerow(
                {
                    "trip_uuid": TRIP_UUID,
                    "full_name": traveler["full_name"],
                    "preferred_name": traveler["preferred_name"],
                    "phone": traveler["phone"],
                    "email": traveler["email"],
                    "package_name": traveler["package_name"],
                    "room_type": traveler["room_type"],
                    "paid_amount_usd": traveler["paid_amount_usd"],
                    "addons": ", ".join(traveler["addons"]) or "none",
                    "user_id": traveler.get("user_id", ""),
                    "trip_traveler_id": traveler.get("trip_traveler_id", ""),
                    "qr_filename": qr_filename(traveler),
                    "qr_drive_url": qr.get("drive_web_view_link", ""),
                }
            )


async def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_dir = Path(args.output_dir)
    database_url = load_env()
    mode = "execute" if args.execute else "dry-run"
    report: dict[str, Any] = {
        "mode": mode,
        "trip_uuid": TRIP_UUID,
        "traveler_count": len(TEST_TRAVELERS),
        "started_at": datetime.now(UTC).isoformat(),
        "sheets": None,
        "drive": None,
    }
    conn = await asyncpg.connect(database_url)
    try:
        before = await discover(conn)
        report["before"] = before
        if args.dry_run:
            report["would_create_or_update"] = {
                "users": len(TEST_TRAVELERS),
                "trip_travelers": len(TEST_TRAVELERS),
                "traveler_profiles": len(TEST_TRAVELERS),
                "traveler_products": len(TEST_TRAVELERS),
                "wetravel_like_orders": len(TEST_TRAVELERS),
                "restricted_activity_rows": {
                    key: len(value) for key, value in build_restricted_activity_allowlists(TEST_TRAVELERS).items()
                },
            }
            write_audit(output_dir, report, [], [])
            print(json.dumps(report["would_create_or_update"], indent=2))
            return
        async with conn.transaction():
            seeded = await upsert_travelers(conn)
        qr_records: list[dict[str, str]] = []
        sheets_report = None
        if not args.skip_drive or not args.skip_sheets:
            sheets, drive = get_google_services(use_oauth=args.use_oauth)
        else:
            sheets = drive = None
        if not args.skip_drive:
            qr_records = generate_and_upload_qrs(drive, seeded, output_dir)
            report["drive"] = {"folder_id": QR_DRIVE_FOLDER_ID, "qr_files": qr_records}
        payload = await fetch_sheet_payload(conn, seeded, qr_records)
        rows = build_sheet_rows(payload)
        if not args.skip_sheets:
            sheets_report = update_sheets(sheets, rows)
            report["sheets"] = sheets_report
        report["after"] = await discover(conn)
        report["seeded_travelers"] = [
            {
                "full_name": traveler["full_name"],
                "phone": traveler["phone"],
                "email": traveler["email"],
                "user_id": traveler["user_id"],
                "trip_traveler_id": traveler["trip_traveler_id"],
                "qr_filename": qr_filename(traveler),
            }
            for traveler in seeded
        ]
        write_audit(output_dir, report, seeded, qr_records)
        print(json.dumps({"seeded": len(seeded), "qr_files": len(qr_records), "sheets_updated": bool(sheets_report)}, indent=2))
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

"""
Seed WeTravel payment/package data for Marcelo test user and generate JWT.

Run from backend directory:
  poetry run python scripts/seed_marcelo_test_user.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from dotenv import load_dotenv
from jose import jwt

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
PG_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"

MARCELO_USER_ID = "e3dae095-7520-4afc-8b67-542e1783ff7d"
MARCELO_PHONE = "+5512991296651"
MARCELO_EMAIL = "angelo@parrottrips.com"
MARCELO_NAME = "Marcelo Angelo da Silva Filho"
TRIP_UUID = "TEST-2026-FULL"
ORDER_ID = "ORDER-TEST-001"

FRONTEND_DEV_USERS_PATH = (
    Path(__file__).parent.parent.parent / "frontend" / "src" / "config" / "devUsers.ts"
)


def _create_jwt(user_id: str, phone: str, role: str = "traveler") -> str:
    expire = datetime.now(UTC) + timedelta(days=90)
    payload = {"sub": user_id, "phone": phone, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def seed(conn: asyncpg.Connection) -> None:
    now = datetime.now(UTC)

    # ── 1. wetravel_bookings ──────────────────────────────────────────────────
    participants_json = json.dumps([
        {
            "id": "TEST-MARCELO-001",
            "full_name": MARCELO_NAME,
            "email": MARCELO_EMAIL,
            "cancelled": False,
        }
    ])

    await conn.execute(
        """
        INSERT INTO wetravel_bookings (
            id, entity_key, order_id, trip_uuid, trip_title, trip_currency,
            buyer_email, buyer_full_name, booking_event_type,
            total_deposit_amount, total_due_amount, total_paid_amount, total_price_amount,
            participant_count, cancelled_participant_count,
            participants_json,
            first_seen_at, inserted_at, row_updated_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
        ON CONFLICT (entity_key) DO UPDATE SET
            total_paid_amount = EXCLUDED.total_paid_amount,
            participants_json = EXCLUDED.participants_json,
            row_updated_at = EXCLUDED.row_updated_at
        """,
        uuid.uuid4(),
        f"booking:{ORDER_ID}",
        ORDER_ID,
        TRIP_UUID,
        "Viagem de Teste — Full Coverage",
        "USD",
        MARCELO_EMAIL,
        MARCELO_NAME,
        "booking_confirmed",
        50000,    # deposit $500.00 (in cents)
        0,        # nothing due
        299900,   # paid $2,999.00
        299900,   # price $2,999.00
        1,
        0,
        participants_json,
        now, now, now,
    )
    print("✓ wetravel_bookings inserted/updated")

    # ── 2. wetravel_payments ─────────────────────────────────────────────────
    await conn.execute(
        """
        INSERT INTO wetravel_payments (
            id, entity_key, payment_id, order_id, trip_uuid, trip_title,
            buyer_email, buyer_full_name,
            status, payment_method, payment_type,
            currency, storage_currency,
            subtotal_amount, total_amount, net_amount,
            payment_processing_fee, refunded_amount, disputed_amount,
            participant_count,
            first_seen_at, inserted_at, row_updated_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23)
        ON CONFLICT (entity_key) DO UPDATE SET
            total_amount = EXCLUDED.total_amount,
            status = EXCLUDED.status,
            row_updated_at = EXCLUDED.row_updated_at
        """,
        uuid.uuid4(),
        f"payment:{ORDER_ID}",
        "PAY-TEST-MARCELO-001",
        ORDER_ID,
        TRIP_UUID,
        "Viagem de Teste — Full Coverage",
        MARCELO_EMAIL,
        MARCELO_NAME,
        "processed",
        "credit_card",
        "full",
        "USD",
        "USD",
        299900,   # subtotal
        299900,   # total
        282905,   # net (after ~5.65% processing fee)
        16995,    # fee
        0,
        0,
        1,
        now, now, now,
    )
    print("✓ wetravel_payments inserted/updated")

    # ── 3. wetravel_order_options ─────────────────────────────────────────────
    options = [
        ("OPT-TEST-PKG-001",    "package",          "Brazil Trek Standard",  199900, 50000),
        ("OPT-TEST-ADDON-001",  "option",            "Airport Transfer",       15000,  5000),
        ("OPT-TEST-ADDON-002",  "option",            "Travel Insurance",       35000, 10000),
        ("OPT-TEST-ADDON-003",  "personal_option",   "eSIM Card",              5000,  1000),
    ]

    for option_id, option_type, option_name, price, deposit in options:
        await conn.execute(
            """
            INSERT INTO wetravel_order_options (
                id, order_id, trip_uuid, option_id, option_type, option_name,
                active_count, cancelled_count, price, deposit_amount,
                synced_at, row_updated_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            ON CONFLICT (order_id, option_id) DO UPDATE SET
                option_name = EXCLUDED.option_name,
                price = EXCLUDED.price,
                row_updated_at = EXCLUDED.row_updated_at
            """,
            uuid.uuid4(),
            ORDER_ID,
            TRIP_UUID,
            option_id,
            option_type,
            option_name,
            1,
            0,
            price,
            deposit,
            now, now,
        )
        print(f"  ✓ option: {option_name} ({option_type})")

    # ── 4. Verify host_trip_participants view ─────────────────────────────────
    print()
    print("=== Verifying host_trip_participants view ===")
    rows = await conn.fetch(
        """
        SELECT htp.trip_uuid, htp.buyer_email, htp.participant_email,
               htp.package_names, htp.addon_names, htp.paid_amount, htp.currency
        FROM host_trip_participants htp
        JOIN wetravel_participant_phones wpp
            ON wpp.email = htp.participant_email
            AND wpp.trip_uuid = htp.trip_uuid
        WHERE wpp.phone = $1 AND wpp.trip_uuid = $2
        """,
        MARCELO_PHONE, TRIP_UUID,
    )
    if rows:
        for r in rows:
            print(f"  trip_uuid:         {r['trip_uuid']}")
            print(f"  participant_email: {r['participant_email']}")
            print(f"  package_names:     {r['package_names']}")
            print(f"  addon_names:       {r['addon_names']}")
            print(f"  paid_amount:       {r['paid_amount']} ({r['currency']})")
            usd = float(r["paid_amount"]) / 100 if r["paid_amount"] else 0
            print(f"  → usd_amount:      ${usd:,.2f}")
    else:
        print("  ⚠️  No rows returned — check joins")

    # ── 5. Generate JWT and devUsers.ts entry ─────────────────────────────────
    token = _create_jwt(MARCELO_USER_ID, MARCELO_PHONE)
    print()
    print("=== devUsers.ts entry for Marcelo ===")
    print("  {")
    print(f"    userId: '{MARCELO_USER_ID}',")
    print(f"    phone: '{MARCELO_PHONE}',")
    print(f"    name: '{MARCELO_NAME}',")
    print(f"    token: '{token}',")
    print(f"    role: 'traveler' as const,")
    print(f"    label: 'Marcelo — TEST-2026-FULL',")
    print(f"    hasData: true,")
    print("  },")

    # ── 6. Append Marcelo entry to devUsers.ts if it exists ──────────────────
    dev_users_path = FRONTEND_DEV_USERS_PATH
    if dev_users_path.exists():
        content = dev_users_path.read_text(encoding="utf-8")
        if MARCELO_USER_ID not in content:
            marcelo_entry = (
                "  {\n"
                f"    userId: '{MARCELO_USER_ID}',\n"
                f"    phone: '{MARCELO_PHONE}',\n"
                f"    name: '{MARCELO_NAME}',\n"
                f"    token: '{token}',\n"
                f"    role: 'traveler' as const,\n"
                f"    label: 'Marcelo — TEST-2026-FULL',\n"
                f"    hasData: true,\n"
                "  },"
            )
            updated = content.replace("] as const;", f"{marcelo_entry}\n] as const;")
            dev_users_path.write_text(updated, encoding="utf-8")
            print()
            print(f"✅ Entry appended to {dev_users_path}")
        else:
            print()
            print(f"ℹ️  Marcelo already in {dev_users_path} (userId found)")
    else:
        print()
        print(f"⚠️  {dev_users_path} does not exist — run gen_dev_users.py first, then re-run this script")


async def main() -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        await seed(conn)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

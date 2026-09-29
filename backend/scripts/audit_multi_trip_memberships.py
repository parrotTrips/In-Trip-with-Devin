"""Read-only audit of multi-trip membership data integrity.

Reports (never writes):
  - duplicate normalized phones (the same real phone number stored differently
    across `users` rows, e.g. one with a leading "+" and one without);
  - `trip_staff` rows missing a matching `trip_travelers` row for the same trip;
  - `trip_travelers`/`trip_staff` memberships whose trip is absent from
    `wetravel_trips`;
  - users with more than one current/future ("eligible") trip and their
    per-trip derived role (traveler vs staff), using the same eligibility rule
    as `app.services.trip_membership_service`;
  - `users.role = 'staff'` accounts with at least one eligible trip membership
    but no `trip_staff` row on those trips — the deploy-time staff loss that
    happens because the old global-role model granted staff access from
    `users.role` alone, and nothing since has backfilled `trip_staff` for them;
  - phones that do not match `scripts._phone.normalize_phone(phone)` — i.e.
    what the importers would have written for that same number today.

This script NEVER reads DATABASE_URL from the environment or a .env file, and it
NEVER writes to the database (every query runs inside a read-only transaction).
You must pass the database URL to audit explicitly on the command line.

Usage:
  cd backend
  poetry run python scripts/audit_multi_trip_memberships.py "postgresql://user@host/db"

Do not point this at a production/remote database from an automated context —
only a human operator deciding to audit a specific database should supply that URL.
"""

from __future__ import annotations

import argparse
import asyncio
import re
from collections import defaultdict
from typing import Any

import asyncpg

from scripts._phone import normalize_phone


def pg_url(database_url: str) -> str:
    """Normalize a SQLAlchemy-style URL to a plain asyncpg-compatible one."""
    return (
        database_url
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgresql+psycopg2://", "postgresql://")
    )


def normalize_phone_digits(phone: str | None) -> str:
    """Digits-only normalization used purely for duplicate DETECTION here.

    This strips every non-digit character (spaces, dashes, parentheses, a
    missing or extra leading "+") so differently formatted representations of
    the same number are grouped together for reporting. It matches what the
    writer-side `scripts._phone.normalize_phone` helper does internally before
    it restores a single leading "+" — see `find_unnormalized_phones` below,
    which compares against that writer helper directly rather than this
    digits-only key.
    """
    return re.sub(r"\D", "", phone or "")


async def find_duplicate_normalized_phones(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT id, phone FROM users WHERE phone IS NOT NULL")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = normalize_phone_digits(row["phone"])
        if not key:
            continue
        groups[key].append({"id": str(row["id"]), "phone": row["phone"]})
    return [
        {"normalized_phone": key, "users": entries}
        for key, entries in sorted(groups.items())
        if len(entries) > 1
    ]


async def find_staff_missing_traveler_link(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT ts.id AS trip_staff_id, ts.wetravel_trip_uuid, ts.user_id, u.phone
        FROM trip_staff ts
        JOIN users u ON u.id = ts.user_id
        LEFT JOIN trip_travelers tt
          ON tt.user_id = ts.user_id AND tt.wetravel_trip_uuid = ts.wetravel_trip_uuid
        WHERE tt.id IS NULL
        ORDER BY ts.wetravel_trip_uuid, u.phone
        """
    )
    return [
        {
            "trip_staff_id": str(r["trip_staff_id"]),
            "trip_uuid": r["wetravel_trip_uuid"],
            "user_id": str(r["user_id"]),
            "phone": r["phone"],
        }
        for r in rows
    ]


async def find_memberships_with_missing_trip(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT 'trip_travelers' AS source, tt.id AS membership_id,
               tt.wetravel_trip_uuid, tt.user_id
        FROM trip_travelers tt
        LEFT JOIN wetravel_trips wt ON wt.trip_uuid = tt.wetravel_trip_uuid
        WHERE wt.trip_uuid IS NULL

        UNION ALL

        SELECT 'trip_staff' AS source, ts.id AS membership_id,
               ts.wetravel_trip_uuid, ts.user_id
        FROM trip_staff ts
        LEFT JOIN wetravel_trips wt ON wt.trip_uuid = ts.wetravel_trip_uuid
        WHERE wt.trip_uuid IS NULL

        ORDER BY wetravel_trip_uuid, source
        """
    )
    return [
        {
            "source": r["source"],
            "membership_id": str(r["membership_id"]),
            "trip_uuid": r["wetravel_trip_uuid"],
            "user_id": str(r["user_id"]),
        }
        for r in rows
    ]


async def find_users_with_multiple_eligible_trips(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Mirrors `trip_membership_service`'s eligibility rule: a trip is eligible
    while it has not ended (no end_date, or end_date >= today). Role is derived
    per trip from the presence of a matching `trip_staff` row, exactly like the
    app does — never from `users.role`.
    """
    rows = await conn.fetch(
        """
        SELECT
            tt.user_id,
            u.phone,
            wt.trip_uuid,
            CASE WHEN ts.id IS NULL THEN 'traveler' ELSE 'staff' END AS role
        FROM trip_travelers tt
        JOIN users u ON u.id = tt.user_id
        JOIN wetravel_trips wt ON wt.trip_uuid = tt.wetravel_trip_uuid
        LEFT JOIN trip_staff ts
          ON ts.wetravel_trip_uuid = tt.wetravel_trip_uuid AND ts.user_id = tt.user_id
        WHERE wt.end_date IS NULL OR wt.end_date >= CURRENT_DATE
        ORDER BY tt.user_id, wt.start_date NULLS LAST
        """
    )
    by_user: dict[str, dict[str, Any]] = {}
    for r in rows:
        user_id = str(r["user_id"])
        entry = by_user.setdefault(user_id, {"phone": r["phone"], "trips": []})
        entry["trips"].append({"trip_uuid": r["trip_uuid"], "role": r["role"]})
    return [
        {"user_id": user_id, "phone": data["phone"], "trips": data["trips"]}
        for user_id, data in by_user.items()
        if len(data["trips"]) > 1
    ]


async def find_users_with_role_staff_missing_trip_staff(
    conn: asyncpg.Connection,
) -> list[dict[str, Any]]:
    """Potential deploy-time staff loss: `users.role = 'staff'` accounts that
    hold at least one eligible trip membership but have no `trip_staff` row in
    any trip.

    Before this rollout, staff access came from `users.role` alone; now it
    requires a per-trip `trip_staff` row. Accounts that already have any such
    row are excluded because a missing row on another trip can intentionally
    mean "traveler here, staff elsewhere". Every reported account still needs
    case-by-case review before any backfill.
    """
    rows = await conn.fetch(
        """
        SELECT u.id AS user_id, u.phone, tt.wetravel_trip_uuid AS trip_uuid
        FROM users u
        JOIN trip_travelers tt ON tt.user_id = u.id
        JOIN wetravel_trips wt ON wt.trip_uuid = tt.wetravel_trip_uuid
        WHERE u.role = 'staff'
          AND (wt.end_date IS NULL OR wt.end_date >= CURRENT_DATE)
          AND NOT EXISTS (
              SELECT 1 FROM trip_staff ts WHERE ts.user_id = u.id
          )
        ORDER BY u.phone, tt.wetravel_trip_uuid
        """
    )
    by_user: dict[str, dict[str, Any]] = {}
    for r in rows:
        user_id = str(r["user_id"])
        entry = by_user.setdefault(
            user_id, {"user_id": user_id, "phone": r["phone"], "trips": []}
        )
        entry["trips"].append(r["trip_uuid"])
    return list(by_user.values())


async def find_unnormalized_phones(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Users whose stored phone does not match what the write-boundary
    normalizer (`scripts._phone.normalize_phone`) would produce for it today —
    i.e. what an importer would have written for that same number.
    """
    rows = await conn.fetch("SELECT id, phone FROM users WHERE phone IS NOT NULL")
    report = []
    for r in rows:
        normalized = normalize_phone(r["phone"])
        if normalized != r["phone"]:
            report.append(
                {
                    "user_id": str(r["id"]),
                    "phone": r["phone"],
                    "normalized_phone": normalized,
                }
            )
    return report


async def run_audit(database_url: str) -> dict[str, Any]:
    conn = await asyncpg.connect(pg_url(database_url))
    try:
        async with conn.transaction(readonly=True):
            duplicate_phones = await find_duplicate_normalized_phones(conn)
            orphaned_staff = await find_staff_missing_traveler_link(conn)
            missing_trip_memberships = await find_memberships_with_missing_trip(conn)
            multi_trip_users = await find_users_with_multiple_eligible_trips(conn)
            role_staff_missing_trip_staff = (
                await find_users_with_role_staff_missing_trip_staff(conn)
            )
            unnormalized_phones = await find_unnormalized_phones(conn)
    finally:
        await conn.close()

    return {
        "duplicate_normalized_phones": duplicate_phones,
        "staff_missing_trip_traveler_link": orphaned_staff,
        "memberships_missing_trip": missing_trip_memberships,
        "users_with_multiple_eligible_trips": multi_trip_users,
        "users_role_staff_missing_trip_staff": role_staff_missing_trip_staff,
        "unnormalized_phones": unnormalized_phones,
    }


def format_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=== Multi-trip membership audit (read-only) ===")

    dup = report["duplicate_normalized_phones"]
    lines.append(f"\nDuplicate normalized phones: {len(dup)}")
    for entry in dup:
        ids = ", ".join(f"{u['id']} ({u['phone']!r})" for u in entry["users"])
        lines.append(f"  - {entry['normalized_phone']}: {ids}")

    orphans = report["staff_missing_trip_traveler_link"]
    lines.append(f"\ntrip_staff rows missing a trip_travelers row: {len(orphans)}")
    for o in orphans:
        lines.append(
            f"  - trip_staff={o['trip_staff_id']} trip={o['trip_uuid']} "
            f"user={o['user_id']} phone={o['phone']}"
        )

    missing = report["memberships_missing_trip"]
    lines.append(f"\nMemberships whose trip is absent from wetravel_trips: {len(missing)}")
    for m in missing:
        lines.append(
            f"  - {m['source']}={m['membership_id']} trip={m['trip_uuid']} user={m['user_id']}"
        )

    multi = report["users_with_multiple_eligible_trips"]
    lines.append(f"\nUsers with multiple eligible trips: {len(multi)}")
    for u in multi:
        trips = ", ".join(f"{t['trip_uuid']}={t['role']}" for t in u["trips"])
        lines.append(f"  - {u['user_id']} ({u['phone']}): {trips}")

    role_staff_missing = report["users_role_staff_missing_trip_staff"]
    lines.append(
        "\nusers.role='staff' with an eligible trip and no trip_staff row anywhere: "
        f"{len(role_staff_missing)}"
    )
    for u in role_staff_missing:
        trips = ", ".join(u["trips"])
        lines.append(f"  - {u['user_id']} ({u['phone']}): {trips}")

    unnormalized = report["unnormalized_phones"]
    lines.append(f"\nPhones that do not match normalize_phone(phone): {len(unnormalized)}")
    for u in unnormalized:
        lines.append(
            f"  - {u['user_id']}: {u['phone']!r} -> {u['normalized_phone']!r}"
        )

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only audit of multi-trip membership data (duplicate phones, "
            "orphaned staff links, dangling trip references, multi-trip users). "
            "Never writes to the database."
        )
    )
    parser.add_argument(
        "database_url",
        help=(
            "Explicit database URL to audit, e.g. postgresql://user@host:5432/db "
            "(postgresql+asyncpg:// is also accepted). This script never reads "
            "DATABASE_URL from the environment or from a .env file — you must pass "
            "it explicitly. Do not point this at a production/remote database from "
            "an automated context."
        ),
    )
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    report = await run_audit(args.database_url)
    print(format_report(report))
    return report


if __name__ == "__main__":
    asyncio.run(main())

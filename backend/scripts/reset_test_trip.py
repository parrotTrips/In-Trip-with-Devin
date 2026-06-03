"""
Full reset of a test trip back to day-zero pre-trip state.

Clears ALL traveler progress (checklist + phase completions), resets in-trip
phase dates to their original sheet values, and sets the trip mode to pre-trip.
Use this after a full end-to-end simulation to start fresh.

Usage:
  cd backend
  poetry run python scripts/reset_test_trip.py --trip-uuid TEST-2026-FULL

  # Preview what will happen without making changes:
  poetry run python scripts/reset_test_trip.py --trip-uuid TEST-2026-FULL --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

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

# Original starts_at dates for TEST-2026-FULL (from the Google Sheet).
# Day 1 = 2026-07-01, Day 2 = 2026-07-02, etc.
ORIGINAL_START_DATE = datetime(2026, 7, 1, 0, 0, 0, tzinfo=UTC)


async def reset(trip_uuid: str, dry_run: bool) -> None:
    conn = await asyncpg.connect(PG_URL)
    tag = "[DRY RUN] " if dry_run else ""

    try:
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        tt_ids = [str(r["id"]) for r in tt_rows]

        checklist_count = await conn.fetchval(
            "SELECT COUNT(*) FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
            tt_ids,
        ) if tt_ids else 0

        phase_progress_count = await conn.fetchval(
            "SELECT COUNT(*) FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
            tt_ids,
        ) if tt_ids else 0

        in_trip_phases = await conn.fetch(
            """
            SELECT id, title, sort_order
            FROM trip_phases
            WHERE wetravel_trip_uuid = $1 AND phase_type = 'in-trip'
            ORDER BY sort_order
            """,
            trip_uuid,
        )

        print(f"\n{'='*60}")
        print(f"  {tag}Full Reset: {trip_uuid}")
        print(f"{'='*60}")
        print(f"  Travelers found:           {len(tt_ids)}")
        print(f"  Checklist progress rows:   {checklist_count}")
        print(f"  Phase progress rows:       {phase_progress_count}")
        print(f"  In-trip phases to redate:  {len(in_trip_phases)}")
        print(f"  New trip mode:             pre-trip")
        print(f"{'='*60}\n")

        if dry_run:
            print("Dry run — no changes made. Remove --dry-run to execute.\n")
            return

        confirm = input("Proceed? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        async with conn.transaction():
            # 1. Clear ALL traveler progress (checklist + phase)
            if tt_ids:
                deleted_checklist = await conn.fetchval(
                    "WITH d AS (DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[]) RETURNING 1) SELECT COUNT(*) FROM d",
                    tt_ids,
                )
                deleted_phase = await conn.fetchval(
                    "WITH d AS (DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[]) RETURNING 1) SELECT COUNT(*) FROM d",
                    tt_ids,
                )
            else:
                deleted_checklist = deleted_phase = 0

            # 2. Reset in-trip phase dates to original sheet values
            for i, phase in enumerate(in_trip_phases):
                from datetime import timedelta
                original_date = ORIGINAL_START_DATE + timedelta(days=i)
                await conn.execute(
                    "UPDATE trip_phases SET starts_at = $1 WHERE id = $2",
                    original_date, phase["id"],
                )

            # 3. Set trip mode to pre-trip
            await conn.execute(
                """
                INSERT INTO trip_settings (trip_uuid, mode)
                VALUES ($1, 'pre-trip')
                ON CONFLICT (trip_uuid) DO UPDATE SET mode = 'pre-trip', updated_at = now()
                """,
                trip_uuid,
            )

        print(f"  ✅ Deleted checklist progress:  {deleted_checklist} rows")
        print(f"  ✅ Deleted phase progress:      {deleted_phase} rows")
        print(f"  ✅ Reset {len(in_trip_phases)} phase dates to 2026-07-01 onwards")
        print(f"  ✅ Trip mode set to:            pre-trip")
        print(f"\nDone. Open the app — should show 📋 Pre-Trip with 0%.\n")

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full reset of a test trip to pre-trip state")
    parser.add_argument("--trip-uuid", required=True, help="WeTravel trip UUID")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()

    asyncio.run(reset(args.trip_uuid, args.dry_run))

"""
Delete all traveler progress (checklist + phase) for a given trip.

Run this ~1 week before trip departure to clear pre-trip progress
so the in-trip phase begins fresh.

Usage:
  cd backend
  poetry run python scripts/reset_traveler_progress.py --trip-uuid gsb-nye-2026

  # Dry run (shows what would be deleted without deleting):
  poetry run python scripts/reset_traveler_progress.py --trip-uuid gsb-nye-2026 --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import os
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


async def reset(trip_uuid: str, dry_run: bool) -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if not tt_rows:
            print(f"No travelers found for trip '{trip_uuid}'.")
            return

        tt_ids = [str(r["id"]) for r in tt_rows]

        checklist_count = await conn.fetchval(
            "SELECT COUNT(*) FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
            tt_ids,
        )
        phase_count = await conn.fetchval(
            "SELECT COUNT(*) FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
            tt_ids,
        )

        print(f"Trip '{trip_uuid}': {len(tt_ids)} traveler(s)")
        print(f"  traveler_checklist_progress rows : {checklist_count}")
        print(f"  traveler_phase_progress rows     : {phase_count}")

        if dry_run:
            print("\nDry run — nothing deleted.")
            return

        confirm = input("\nProceed with deletion? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        async with conn.transaction():
            await conn.execute(
                "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                tt_ids,
            )
            await conn.execute(
                "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                tt_ids,
            )

        print(f"\nDeleted {checklist_count} checklist + {phase_count} phase progress rows.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset traveler progress for a trip")
    parser.add_argument("--trip-uuid", required=True, help="WeTravel trip UUID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()
    asyncio.run(reset(args.trip_uuid, args.dry_run))

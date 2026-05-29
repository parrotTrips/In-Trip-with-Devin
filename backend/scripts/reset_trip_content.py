"""
Delete all trip_phases data (and dependent rows) from the database.

This removes everything imported via the Google Sheets pipeline:
  - traveler_checklist_progress
  - traveler_phase_progress
  - trip_activities
  - trip_phase_checklist_items
  - trip_phase_links
  - trip_phases

WeTravel data (wetravel_trips, trip_travelers, users) is NOT touched.

Usage:
  cd backend
  poetry run python scripts/reset_trip_content.py

  # Dry run — shows what would be deleted without actually deleting:
  poetry run python scripts/reset_trip_content.py --dry-run

  # Limit to a single trip:
  poetry run python scripts/reset_trip_content.py --trip-uuid gsb-nye-2026
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


async def reset(trip_uuid: str | None, dry_run: bool) -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        if trip_uuid:
            phase_rows = await conn.fetch(
                "SELECT id, wetravel_trip_uuid FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
            )
        else:
            phase_rows = await conn.fetch("SELECT id, wetravel_trip_uuid FROM trip_phases")

        if not phase_rows:
            print("No trip_phases rows found — nothing to delete.")
            return

        phase_ids = [str(r["id"]) for r in phase_rows]
        print(f"trip_phases to delete: {len(phase_ids)}")

        # Count dependent rows
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = ANY($1::text[])",
            list({r["wetravel_trip_uuid"] for r in phase_rows}) if not trip_uuid
            else [trip_uuid],
        ) if not trip_uuid else await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        tt_ids = [str(r["id"]) for r in tt_rows]

        counts: dict[str, int] = {}
        if tt_ids:
            counts["traveler_checklist_progress"] = await conn.fetchval(
                "SELECT COUNT(*) FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                tt_ids,
            )
            counts["traveler_phase_progress"] = await conn.fetchval(
                "SELECT COUNT(*) FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                tt_ids,
            )
        counts["trip_activities"] = await conn.fetchval(
            "SELECT COUNT(*) FROM trip_activities WHERE trip_phase_id = ANY($1::uuid[])",
            phase_ids,
        )
        counts["trip_phase_checklist_items"] = await conn.fetchval(
            "SELECT COUNT(*) FROM trip_phase_checklist_items WHERE trip_phase_id = ANY($1::uuid[])",
            phase_ids,
        )
        counts["trip_phase_links"] = await conn.fetchval(
            "SELECT COUNT(*) FROM trip_phase_links WHERE trip_phase_id = ANY($1::uuid[])",
            phase_ids,
        )
        counts["trip_phases"] = len(phase_ids)

        print("Rows to be deleted:")
        for table, count in counts.items():
            print(f"  {table}: {count}")

        if dry_run:
            print("\nDry run — nothing deleted.")
            return

        confirm = input("\nProceed with deletion? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        async with conn.transaction():
            if tt_ids:
                await conn.execute(
                    "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
                await conn.execute(
                    "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
            await conn.execute(
                "DELETE FROM trip_activities WHERE trip_phase_id = ANY($1::uuid[])",
                phase_ids,
            )
            await conn.execute(
                "DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = ANY($1::uuid[])",
                phase_ids,
            )
            await conn.execute(
                "DELETE FROM trip_phase_links WHERE trip_phase_id = ANY($1::uuid[])",
                phase_ids,
            )
            if trip_uuid:
                await conn.execute(
                    "DELETE FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
                )
            else:
                await conn.execute("DELETE FROM trip_phases")

        print("\nDone.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset trip_phases data from the database")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    parser.add_argument("--trip-uuid", help="Limit reset to a single trip UUID")
    args = parser.parse_args()
    asyncio.run(reset(args.trip_uuid, args.dry_run))

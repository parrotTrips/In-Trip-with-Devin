"""
Simulate trip progress by adjusting in-trip phase starts_at dates.

Sets the starts_at of each in-trip day so that exactly N days appear as
"already started" — allowing visual testing of the progress bar without
waiting for real days to pass.

Usage:
  cd backend

  # Show current state (dry run)
  poetry run python scripts/simulate_trip_day.py --trip-uuid TEST-2026-FULL --day 0

  # Simulate Day 1 just started (bar at ~14%)
  poetry run python scripts/simulate_trip_day.py --trip-uuid TEST-2026-FULL --day 1

  # Simulate Day 4 (bar at ~57%)
  poetry run python scripts/simulate_trip_day.py --trip-uuid TEST-2026-FULL --day 4

  # Simulate all days done (bar at 100%)
  poetry run python scripts/simulate_trip_day.py --trip-uuid TEST-2026-FULL --day 7

  # Reset to original dates from the sheet (undoes simulation)
  poetry run python scripts/simulate_trip_day.py --trip-uuid TEST-2026-FULL --reset
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import UTC, date, datetime, timedelta
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


def validate_target_day(target_day: int, total_days: int) -> None:
    if target_day < 0 or target_day > total_days:
        raise ValueError(f"Day must be between 0 and {total_days}. Received: {target_day}")


def calculate_simulated_starts_at(day_num: int, target_day: int, now: datetime) -> datetime:
    if day_num <= target_day:
        return now - timedelta(days=(target_day - day_num + 1))
    return now + timedelta(days=(day_num - target_day))


def calculate_reset_starts_at(trip_start: date, day_num: int) -> datetime:
    return datetime.combine(trip_start + timedelta(days=day_num - 1), datetime.min.time(), tzinfo=UTC)


async def simulate(trip_uuid: str, target_day: int) -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        phases = await conn.fetch(
            """
            SELECT id, title, sort_order, starts_at
            FROM trip_phases
            WHERE wetravel_trip_uuid = $1 AND phase_type = 'in-trip'
            ORDER BY sort_order
            """,
            trip_uuid,
        )

        if not phases:
            print(f"No in-trip phases found for trip '{trip_uuid}'.")
            return

        total = len(phases)
        validate_target_day(target_day, total)
        print(f"\nTrip: {trip_uuid} | {total} in-trip days | simulating Day {target_day}/{total}")
        print(f"Progress bar will show: {target_day}/{total} = {round(target_day/total*100)}%\n")

        now = datetime.now(UTC)

        for i, phase in enumerate(phases):
            day_num = i + 1
            new_starts_at = calculate_simulated_starts_at(day_num, target_day, now)
            if day_num <= target_day:
                status = "✅ STARTED"
            else:
                status = "⏳ future"

            await conn.execute(
                "UPDATE trip_phases SET starts_at = $1 WHERE id = $2",
                new_starts_at, phase["id"],
            )
            print(f"  Day {day_num}: {phase['title'][:40]:<40} {status}  → {new_starts_at.strftime('%Y-%m-%d %H:%M')} UTC")

        print(f"\n✅ Done. Open the app and refresh to see Day {target_day} on the progress bar.")
        print(f"   Bar should show: {round(target_day/total*100)}%")
    finally:
        await conn.close()


async def reset_dates(trip_uuid: str) -> None:
    """Restore starts_at from the trip start date (date only, midnight UTC)."""
    conn = await asyncpg.connect(PG_URL)
    try:
        trip_start = await conn.fetchval(
            "SELECT start_date FROM wetravel_trips WHERE trip_uuid = $1",
            trip_uuid,
        )
        if not trip_start:
            print(f"No start_date found for trip '{trip_uuid}'. Reset aborted.")
            return
        if isinstance(trip_start, datetime):
            trip_start = trip_start.date()

        phases = await conn.fetch(
            """
            SELECT id, title, sort_order, starts_at
            FROM trip_phases
            WHERE wetravel_trip_uuid = $1 AND phase_type = 'in-trip'
            ORDER BY sort_order
            """,
            trip_uuid,
        )

        if not phases:
            print(f"No in-trip phases found for trip '{trip_uuid}'.")
            return

        print(f"\nResetting {len(phases)} in-trip phases from trip start date {trip_start}...\n")
        for i, phase in enumerate(phases):
            original_date = calculate_reset_starts_at(trip_start, i + 1)
            await conn.execute(
                "UPDATE trip_phases SET starts_at = $1 WHERE id = $2",
                original_date, phase["id"],
            )
            print(f"  Day {i+1}: {phase['title'][:40]:<40} → {original_date.strftime('%Y-%m-%d')}")

        print("\n✅ Dates reset to original values.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate trip day progress for testing")
    parser.add_argument("--trip-uuid", required=True, help="WeTravel trip UUID")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--day", type=int, help="Simulate N days having passed (0 = none started)")
    group.add_argument("--reset", action="store_true", help="Reset dates to original sheet values")
    args = parser.parse_args()

    if args.reset:
        try:
            asyncio.run(reset_dates(args.trip_uuid))
        except ValueError as exc:
            print(f"ERROR: {exc}")
    else:
        try:
            asyncio.run(simulate(args.trip_uuid, args.day))
        except ValueError as exc:
            print(f"ERROR: {exc}")

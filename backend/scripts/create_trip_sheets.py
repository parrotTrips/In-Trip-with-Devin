"""
Create one Google Sheets file per trip in a specified Google Drive folder.

Each spreadsheet has three tabs:
  - Config    : trip metadata (auto-filled from the database)
  - Pre-Trip  : pre-trip phases template (visa, vaccination, packing, documents)
  - Roteiro   : day-by-day itinerary template

Usage:
  cd backend
  poetry run python scripts/create_trip_sheets.py --folder-id <GOOGLE_DRIVE_FOLDER_ID>

Prerequisites:
  - GCP_SERVICE_ACCOUNT_JSON set in backend/.env (path to service account key)
  - Service account must have Editor access to the target Google Drive folder
  - Google Sheets API and Google Drive API must be enabled in the GCP project
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
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

GCP_SERVICE_ACCOUNT_JSON = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "")


async def fetch_trips(conn: asyncpg.Connection) -> list[dict]:
    """Return all trips ordered by start_date."""
    rows = await conn.fetch(
        "SELECT trip_uuid, title, start_date, end_date FROM wetravel_trips ORDER BY start_date NULLS LAST"
    )
    return [dict(r) for r in rows]


def _sheet_name(trip: dict) -> str:
    """Canonical spreadsheet name for a trip."""
    date_str = trip["start_date"].strftime("%Y-%m-%d") if trip["start_date"] else "0000-00-00"
    title = (trip["title"] or "Unnamed Trip")[:50]
    return f"{date_str} {trip['trip_uuid']} — {title}"


async def main(folder_id: str) -> None:
    if not GCP_SERVICE_ACCOUNT_JSON:
        print("ERROR: GCP_SERVICE_ACCOUNT_JSON is not set in backend/.env")
        sys.exit(1)

    sa_path = Path(__file__).parent.parent / GCP_SERVICE_ACCOUNT_JSON
    if not sa_path.exists():
        print(f"ERROR: Service account file not found: {sa_path}")
        sys.exit(1)

    print("Connecting to database...")
    conn = await asyncpg.connect(PG_URL)
    try:
        trips = await fetch_trips(conn)
    finally:
        await conn.close()

    print(f"Trips found: {len(trips)}")
    for t in trips:
        print(f"  - {_sheet_name(t)}")

    # Google API calls come in Task 3
    print("\n(Google API integration not yet implemented)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create trip content spreadsheets in Google Drive")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID")
    args = parser.parse_args()
    asyncio.run(main(args.folder_id))

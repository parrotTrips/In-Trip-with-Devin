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
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

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


def build_clients(sa_path: Path):
    """Return (sheets_service, drive_service) authenticated with the service account."""
    creds = service_account.Credentials.from_service_account_file(
        str(sa_path), scopes=SCOPES
    )
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return sheets, drive


def list_existing_names(drive, folder_id: str) -> set[str]:
    """Return the set of file names already present in the Drive folder."""
    existing: set[str] = set()
    page_token = None
    while True:
        resp = (
            drive.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(name)",
                pageToken=page_token,
            )
            .execute()
        )
        for f in resp.get("files", []):
            existing.add(f["name"])
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return existing


def _sheet_name(trip: dict) -> str:
    """Canonical spreadsheet name for a trip."""
    date_str = trip["start_date"].strftime("%Y-%m-%d") if trip["start_date"] else "0000-00-00"
    title = (trip["title"] or "Unnamed Trip")[:50]
    return f"{date_str} {trip['trip_uuid']} — {title}"


def create_spreadsheet(sheets_svc, drive_svc, folder_id: str, name: str) -> str:
    """Create an empty spreadsheet with the given name, move it to folder_id, return its ID."""
    body = {"properties": {"title": name}}
    resp = sheets_svc.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    spreadsheet_id = resp["spreadsheetId"]

    # Move from root ("My Drive") to target folder
    file_meta = drive_svc.files().get(fileId=spreadsheet_id, fields="parents").execute()
    previous_parents = ",".join(file_meta.get("parents", []))
    drive_svc.files().update(
        fileId=spreadsheet_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields="id, parents",
    ).execute()

    return spreadsheet_id


def populate_config_tab(sheets_svc, spreadsheet_id: str, trip: dict) -> None:
    """Fill the first (default) sheet with Config data and rename it to 'Config'."""
    start_date = trip["start_date"].strftime("%Y-%m-%d") if trip["start_date"] else ""
    end_date = trip["end_date"].strftime("%Y-%m-%d") if trip["end_date"] else ""

    # Rename sheet 1 to "Config"
    first_sheet_id = _get_first_sheet_id(sheets_svc, spreadsheet_id)
    requests = [
        {
            "updateSheetProperties": {
                "properties": {"sheetId": first_sheet_id, "title": "Config"},
                "fields": "title",
            }
        }
    ]
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()

    # Write header row + data rows
    values = [
        ["chave", "valor"],
        ["trip_uuid", trip["trip_uuid"]],
        ["trip_title", trip["title"] or ""],
        ["start_date", start_date],
        ["end_date", end_date],
    ]
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Config!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    # Bold the header row and freeze it
    _apply_header_formatting(sheets_svc, spreadsheet_id, first_sheet_id, num_cols=2)


def _get_first_sheet_id(sheets_svc, spreadsheet_id: str) -> int:
    """Return the sheetId of the first sheet."""
    meta = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return meta["sheets"][0]["properties"]["sheetId"]


def _apply_header_formatting(sheets_svc, spreadsheet_id: str, sheet_id: int, num_cols: int) -> None:
    """Bold row 1 and freeze it for the given sheet."""
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols,
                },
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        },
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()


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

    print("\nConnecting to Google APIs...")
    sheets_svc, drive_svc = build_clients(sa_path)

    print(f"Listing existing files in folder {folder_id}...")
    existing_names = list_existing_names(drive_svc, folder_id)
    print(f"  Found {len(existing_names)} existing file(s)")

    created = 0
    skipped = 0
    urls = []

    for trip in trips:
        name = _sheet_name(trip)
        if name in existing_names:
            print(f"  ⏭  Skipped (already exists): {name}")
            skipped += 1
            continue

        print(f"  ✅ Creating: {name}...")
        spreadsheet_id = create_spreadsheet(sheets_svc, drive_svc, folder_id, name)
        populate_config_tab(sheets_svc, spreadsheet_id, trip)
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        urls.append((name, url))
        created += 1

    print(f"\nDone: {created} created, {skipped} skipped")
    for name, url in urls:
        print(f"  {name}\n    {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create trip content spreadsheets in Google Drive")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID")
    args = parser.parse_args()
    asyncio.run(main(args.folder_id))

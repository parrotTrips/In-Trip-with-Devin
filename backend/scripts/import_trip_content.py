"""
Read a filled Google Sheets spreadsheet for a single trip and upsert its
content into Supabase (trip_phases, checklist_items, links, activities).

Usage:
  cd backend
  poetry run python scripts/import_trip_content.py --sheet-id <SPREADSHEET_ID>

The SPREADSHEET_ID is the long ID in the sheet URL:
  https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit

Prerequisites:
  - secrets/gcp-oauth2-credentials.json  (OAuth2 Desktop app client)
  - secrets/gcp-oauth2-token.json        (auto-created on first run)
  - DATABASE_URL in backend/.env
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

_TOKEN_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-token.json"
_OAUTH2_CREDS_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-credentials.json"

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


def _get_credentials() -> Credentials:
    creds: Credentials | None = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not _OAUTH2_CREDS_FILE.exists():
                print(f"ERROR: OAuth2 credentials file not found: {_OAUTH2_CREDS_FILE}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(_OAUTH2_CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_FILE.write_text(creds.to_json())
    return creds


def build_sheets_client():
    return build("sheets", "v4", credentials=_get_credentials())


def read_tab(sheets_svc, sheet_id: str, tab_name: str) -> list[list[str]]:
    """Return all rows of a tab as list-of-lists (strings). Empty cells become ''."""
    resp = (
        sheets_svc.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=tab_name)
        .execute()
    )
    return resp.get("values", [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import trip content from a Google Sheets spreadsheet into Supabase"
    )
    parser.add_argument(
        "--sheet-id",
        required=True,
        help="Google Sheets spreadsheet ID (from the URL: /spreadsheets/d/<ID>/edit)",
    )
    args = parser.parse_args()
    print(f"Sheet ID: {args.sheet_id} (implementation coming in later tasks)")

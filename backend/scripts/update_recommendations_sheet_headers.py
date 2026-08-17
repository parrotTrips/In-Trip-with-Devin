"""Ensure the Recomendacoes sheet tab has rich recommendation columns.

This is a non-destructive helper: it appends missing header columns to row 1
and leaves all existing recommendation rows untouched.
"""

from __future__ import annotations

import os
from pathlib import Path

import google.auth
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv(Path(__file__).parent.parent / ".env")

TRIP_CONTENT_SHEET_ID = os.environ.get("TRIP_CONTENT_SHEET_ID", "")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = Path(__file__).parent.parent / "secrets" / "gcp-service-account.json"

RECOMMENDATIONS_HEADERS = [
    "trip_uuid",
    "name",
    "description",
    "address",
    "photo_url",
    "sort_order",
    "category",
    "neighborhood",
    "location",
    "highlight",
    "price_range",
    "rating",
    "map_url",
    "emoji",
    "phone",
    "whatsapp_url",
    "contact_label",
]


def column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def main() -> None:
    if not TRIP_CONTENT_SHEET_ID:
        raise SystemExit("TRIP_CONTENT_SHEET_ID is not set")

    if SERVICE_ACCOUNT_FILE.exists():
        creds = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE),
            scopes=SCOPES,
        )
    else:
        creds, _ = google.auth.default(scopes=SCOPES)
    sheets = build("sheets", "v4", credentials=creds)

    result = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=TRIP_CONTENT_SHEET_ID, range="Recomendacoes!1:1")
        .execute()
    )
    current = result.get("values", [[]])[0]
    current_lower = {header.strip().lower() for header in current}
    missing = [header for header in RECOMMENDATIONS_HEADERS if header not in current_lower]

    if not missing:
        print("Recomendacoes headers already include all rich recommendation columns.")
        return

    updated = current + missing
    end_col = column_name(len(updated))
    (
        sheets.spreadsheets()
        .values()
        .update(
            spreadsheetId=TRIP_CONTENT_SHEET_ID,
            range=f"Recomendacoes!A1:{end_col}1",
            valueInputOption="RAW",
            body={"values": [updated]},
        )
        .execute()
    )
    print("Added missing Recomendacoes headers: " + ", ".join(missing))


if __name__ == "__main__":
    main()

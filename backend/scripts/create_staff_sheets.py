"""
Create the Staff Google Sheets spreadsheet in a Google Drive folder.

The spreadsheet has three tabs:
  - Viagens  : reference list of active trips (populated by Sync Trips in CodeStaff.gs)
  - Contatos : contacts per trip (local guides, accommodation, transport, emergency)
  - Staff    : staff members per trip (reference — roles are managed via the menu)
  - Tarefas Staff : operational staff tasks per itinerary activity

Usage:
  gcloud auth application-default login
  cd backend
  poetry run python scripts/create_staff_sheets.py --folder-id <GOOGLE_DRIVE_FOLDER_ID> --use-adc

Prerequisites:
  - Google Sheets API and Google Drive API must be enabled in the GCP project
  - Run `gcloud auth application-default login` before running with --use-adc
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "Parrot Trips — Staff"

VIAGENS_HEADER = ["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim"]

CONTATOS_HEADER = ["trip_uuid", "category", "name", "role", "phone", "sort_order"]

STAFF_HEADER = ["phone", "nome", "funcao", "trip_uuid"]

STAFF_TASKS_HEADER = [
    "trip_uuid",
    "dia",
    "atividade_nome",
    "staff_phone",
    "titulo",
    "descricao",
    "sort_order",
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

GCP_SERVICE_ACCOUNT_JSON = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "")


# ── Example rows ──────────────────────────────────────────────────────────────

def _contatos_example_rows(trip_uuid: str) -> list[list]:
    u = trip_uuid
    return [
        [u, "Local guides",  "Carlos Mendoza",         "Lead guide",       "+55 11 91234-0001", 1],
        [u, "Local guides",  "Ana Torres",              "Naturalist guide", "+55 11 91234-0002", 2],
        [u, "Accommodation", "Hotel Exemplo",           "Front desk",       "+55 11 3000-0001",  1],
        [u, "Transport",     "Transfer Parrot",         "Driver — João",    "+55 11 91234-0003", 1],
        [u, "Emergency",     "Hospital local",          "Pronto-socorro",   "+55 11 3000-0002",  1],
        [u, "Emergency",     "Parrot Trips HQ",         "24h emergency",    "+55 11 91234-5678", 2],
    ]


def _staff_example_rows(trip_uuid: str) -> list[list]:
    u = trip_uuid
    return [
        ["+55 11 99999-0001", "Guia Exemplo 1", "Lead Guide",       u],
        ["+55 11 99999-0002", "Guia Exemplo 2", "Support Guide",    u],
    ]


def _staff_tasks_example_rows(trip_uuid: str) -> list[list]:
    u = trip_uuid
    return [
        [
            u,
            1,
            "Airport Transfer",
            "+55 11 99999-0001",
            "Coordenar van 1",
            "Receber viajantes no aeroporto e direcionar para a van correta",
            1,
        ],
        [
            u,
            1,
            "Airport Transfer",
            "+55 11 99999-0002",
            "Confirmar fornecedor",
            "Falar com motorista e confirmar saída",
            1,
        ],
    ]


# ── Google API helpers ────────────────────────────────────────────────────────

def _get_oauth2_credentials() -> Credentials:
    creds = None
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


def build_clients(use_adc: bool):
    if use_adc:
        creds = _get_oauth2_credentials()
    else:
        if not GCP_SERVICE_ACCOUNT_JSON:
            print("ERROR: GCP_SERVICE_ACCOUNT_JSON not set. Use --use-adc instead.")
            sys.exit(1)
        sa_path = Path(__file__).parent.parent / GCP_SERVICE_ACCOUNT_JSON
        creds = service_account.Credentials.from_service_account_file(str(sa_path), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds), build("drive", "v3", credentials=creds)


def list_files_in_folder(drive, folder_id: str) -> list[dict]:
    files, page_token = [], None
    while True:
        resp = drive.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name)",
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def create_spreadsheet(sheets_svc, drive_svc, folder_id: str, name: str) -> str:
    resp = sheets_svc.spreadsheets().create(
        body={"properties": {"title": name}}, fields="spreadsheetId"
    ).execute()
    sid = resp["spreadsheetId"]
    meta = drive_svc.files().get(fileId=sid, fields="parents", supportsAllDrives=True).execute()
    drive_svc.files().update(
        fileId=sid,
        addParents=folder_id,
        removeParents=",".join(meta.get("parents", [])),
        fields="id, parents",
        supportsAllDrives=True,
    ).execute()
    return sid


def _get_first_sheet_id(sheets_svc, spreadsheet_id: str) -> int:
    meta = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return meta["sheets"][0]["properties"]["sheetId"]


def _apply_header_formatting(sheets_svc, spreadsheet_id: str, sheet_id: int, num_cols: int) -> None:
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
                               "startColumnIndex": 0, "endColumnIndex": num_cols},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat.textFormat.bold",
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount",
                }
            },
        ]},
    ).execute()


def populate_spreadsheet(sheets_svc, spreadsheet_id: str, trips: list[dict]) -> None:
    first_sheet_id = _get_first_sheet_id(sheets_svc, spreadsheet_id)

    # Rename first tab to Viagens
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"updateSheetProperties": {
            "properties": {"sheetId": first_sheet_id, "title": "Viagens"},
            "fields": "title",
        }}]},
    ).execute()

    # Viagens tab
    def fmt_date(d) -> str:
        return (d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]) if d else ""

    viagens_values = [VIAGENS_HEADER] + [
        [t["trip_uuid"], t["title"] or "", fmt_date(t["start_date"]), fmt_date(t["end_date"])]
        for t in trips
    ]
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range="Viagens!A1",
        valueInputOption="RAW", body={"values": viagens_values},
    ).execute()
    _apply_header_formatting(sheets_svc, spreadsheet_id, first_sheet_id, num_cols=len(VIAGENS_HEADER))

    def _add_tab(title: str, header: list, rows: list) -> None:
        resp = sheets_svc.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
        ).execute()
        sheet_id = resp["replies"][0]["addSheet"]["properties"]["sheetId"]
        sheets_svc.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f"{title}!A1",
            valueInputOption="RAW", body={"values": [header] + rows},
        ).execute()
        _apply_header_formatting(sheets_svc, spreadsheet_id, sheet_id, num_cols=len(header))
        time.sleep(0.5)

    contatos_rows, staff_rows, staff_tasks_rows = [], [], []
    for trip in trips:
        u = trip["trip_uuid"]
        contatos_rows.extend(_contatos_example_rows(u))
        staff_rows.extend(_staff_example_rows(u))
        staff_tasks_rows.extend(_staff_tasks_example_rows(u))

    _add_tab("Contatos", CONTATOS_HEADER, contatos_rows)
    _add_tab("Staff",    STAFF_HEADER,    staff_rows)
    _add_tab("Tarefas Staff", STAFF_TASKS_HEADER, staff_tasks_rows)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(folder_id: str, use_adc: bool) -> None:
    print("Connecting to database...")
    conn = await asyncpg.connect(PG_URL)
    try:
        rows = await conn.fetch(
            "SELECT trip_uuid, title, start_date, end_date FROM wetravel_trips ORDER BY start_date NULLS LAST"
        )
        trips = [dict(r) for r in rows]
    finally:
        await conn.close()

    print(f"Trips found: {len(trips)}")
    for t in trips:
        print(f"  - {t['trip_uuid']} ({t['title']})")

    print("\nConnecting to Google APIs...")
    sheets_svc, drive_svc = build_clients(use_adc)

    print(f"Listing files in folder {folder_id}...")
    existing = {f["name"]: f["id"] for f in list_files_in_folder(drive_svc, folder_id)}

    if SHEET_NAME in existing:
        spreadsheet_id = existing[SHEET_NAME]
        print(f"\n⏭  Spreadsheet already exists — skipping creation.")
        print(f"   To repopulate it, delete it from Drive and re-run this script.")
    else:
        print(f"\n✅ Creating: {SHEET_NAME}...")
        spreadsheet_id = create_spreadsheet(sheets_svc, drive_svc, folder_id, SHEET_NAME)
        populate_spreadsheet(sheets_svc, spreadsheet_id, trips)

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    print(f"   {url}")
    print(f"\nDone. Sheet ID: {spreadsheet_id}")
    print(f"Add to backend/.env:  STAFF_CONTENT_SHEET_ID={spreadsheet_id}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create the Staff spreadsheet in Google Drive")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID")
    parser.add_argument("--use-adc", action="store_true",
                        help="Use Application Default Credentials (your own Google account). "
                             "Run `gcloud auth application-default login` first.")
    args = parser.parse_args()
    asyncio.run(main(args.folder_id, use_adc=args.use_adc))

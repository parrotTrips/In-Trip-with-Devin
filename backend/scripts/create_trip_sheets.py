"""
Create one Google Sheets file per trip in a specified Google Drive folder.

Each spreadsheet has three tabs:
  - Config    : trip metadata (auto-filled from the database)
  - Pre-Trip  : pre-trip phases template (visa, vaccination, packing, documents)
  - Roteiro   : day-by-day itinerary template

Usage (recommended — your own Google account):
  gcloud auth application-default login
  cd backend
  poetry run python scripts/create_trip_sheets.py --folder-id <GOOGLE_DRIVE_FOLDER_ID> --use-adc

Usage (service account):
  cd backend
  poetry run python scripts/create_trip_sheets.py --folder-id <GOOGLE_DRIVE_FOLDER_ID>

Prerequisites:
  - Google Sheets API and Google Drive API must be enabled in the GCP project
  - For --use-adc: run `gcloud auth application-default login` first
  - For service account: GCP_SERVICE_ACCOUNT_JSON set in backend/.env
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    # drive scope needed to list all files in folder (idempotency) and move created sheets into folder.
    # Restrict access by sharing the target folder only with this service account.
    "https://www.googleapis.com/auth/drive",
]

PRE_TRIP_HEADER = ["fase", "bloco", "ordem", "campo", "valor"]

PRE_TRIP_EXAMPLE_ROWS: list[list[str]] = [
    # visa — header
    ["visa", "header", "1", "title", "Visto"],
    ["visa", "header", "1", "subtitle", "Requisitos de entrada para o Brasil"],
    ["visa", "header", "1", "icon", "passport"],
    ["visa", "header", "1", "short_description", "Verifique os requisitos de visto para sua nacionalidade."],
    ["visa", "header", "1", "detailed_description", "Cidadãos americanos precisam de eVisa para o Brasil. Solicite com antecedência."],
    # visa — checklist
    ["visa", "checklist", "1", "label", "Verificar se sua nacionalidade requer visto"],
    ["visa", "checklist", "1", "is_required", "true"],
    ["visa", "checklist", "2", "label", "Solicitar eVisa no portal oficial (se aplicável)"],
    ["visa", "checklist", "2", "is_required", "true"],
    # visa — links
    ["visa", "link", "1", "label", "Portal eVisa Brasil"],
    ["visa", "link", "1", "url", "https://www.gov.br/mre/pt-br/assuntos/portal-consular/vistos"],
    # vaccination — header
    ["vaccination", "header", "1", "title", "Vacinas"],
    ["vaccination", "header", "1", "subtitle", "Requisitos de saúde para viagem"],
    ["vaccination", "header", "1", "icon", "syringe"],
    ["vaccination", "header", "1", "short_description", "Vacinas obrigatórias e recomendadas para o Brasil."],
    ["vaccination", "header", "1", "detailed_description", "Febre amarela é fortemente recomendada. Consulte o CDC para recomendações atualizadas."],
    # vaccination — checklist
    ["vaccination", "checklist", "1", "label", "Tomar vacina de febre amarela"],
    ["vaccination", "checklist", "1", "is_required", "true"],
    ["vaccination", "checklist", "2", "label", "Obter carteira de vacinação internacional"],
    ["vaccination", "checklist", "2", "is_required", "false"],
    # vaccination — links
    ["vaccination", "link", "1", "label", "CDC — Brasil"],
    ["vaccination", "link", "1", "url", "https://wwwnc.cdc.gov/travel/destinations/traveler/none/brazil"],
    # packing — header
    ["packing", "header", "1", "title", "Como Arrumar a Mala"],
    ["packing", "header", "1", "subtitle", "O que levar na viagem"],
    ["packing", "header", "1", "icon", "luggage"],
    ["packing", "header", "1", "short_description", "Dicas de bagagem para o Brasil."],
    ["packing", "header", "1", "detailed_description", "Climate quente e úmido. Leve roupas leves, protetor solar e adaptador de tomada (Tipo N)."],
    # packing — checklist
    ["packing", "checklist", "1", "label", "Roupas leves e respiráveis"],
    ["packing", "checklist", "1", "is_required", "false"],
    ["packing", "checklist", "2", "label", "Protetor solar FPS 50+"],
    ["packing", "checklist", "2", "is_required", "false"],
    # packing — links
    ["packing", "link", "1", "label", "Guia de tomadas do Brasil"],
    ["packing", "link", "1", "url", "https://www.power-plugs-sockets.com/brazil/"],
    # documents — header
    ["documents", "header", "1", "title", "Documentos"],
    ["documents", "header", "1", "subtitle", "Documentos de viagem necessários"],
    ["documents", "header", "1", "icon", "file-text"],
    ["documents", "header", "1", "short_description", "Todos os documentos essenciais para a viagem."],
    ["documents", "header", "1", "detailed_description", "Mantenha cópias digitais e impressas. Passaporte com validade de 6+ meses além da viagem."],
    # documents — checklist
    ["documents", "checklist", "1", "label", "Passaporte válido (6+ meses de validade)"],
    ["documents", "checklist", "1", "is_required", "true"],
    ["documents", "checklist", "2", "label", "Aprovação de visto impressa"],
    ["documents", "checklist", "2", "is_required", "true"],
    # documents — links
    ["documents", "link", "1", "label", "Guia de seguro viagem"],
    ["documents", "link", "1", "url", "https://www.gov.br/turismo/pt-br"],
]

ROTEIRO_HEADER = [
    "dia",
    "data",
    "dia_titulo",
    "dia_subtitulo",
    "dia_icon",
    "dia_descricao_curta",
    "dia_descricao_completa",
    "atividade_nome",
    "atividade_tipo",
    "atividade_horario",
    "atividade_duracao_min",
    "atividade_descricao_curta",
    "atividade_info_pratica",
    "atividade_preco_brl",
]

ROTEIRO_EXAMPLE_ROWS: list[list[str]] = [
    [
        "1",                                        # dia
        "YYYY-MM-DD",                               # data
        "Day 1 — Dec 26",                           # dia_titulo
        "Chegada",                                  # dia_subtitulo
        "plane-landing",                            # dia_icon
        "Transfer do aeroporto e check-in no hotel",# dia_descricao_curta
        "Bem-vindos! Você será recebido no aeroporto e levado ao hotel. À noite, Welcome Happy Hour.",  # dia_descricao_completa
        "Transfer do Aeroporto",                    # atividade_nome
        "logistics",                                # atividade_tipo (included/optional/suggested/logistics)
        "",                                         # atividade_horario  (ex: 10:00)
        "",                                         # atividade_duracao_min (ex: 120)
        "Recepção no aeroporto conforme formulário de pré-viagem.",  # atividade_descricao_curta
        "Procurar placa com o nome da Parrot Trips na área de desembarque.",  # atividade_info_pratica
        "",                                         # atividade_preco_brl (só para opcional)
    ],
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


_TOKEN_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-token.json"
_OAUTH2_CREDS_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-credentials.json"


def _get_oauth2_credentials() -> Credentials:
    """Return OAuth2 credentials, refreshing or prompting as needed."""
    creds: Credentials | None = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not _OAUTH2_CREDS_FILE.exists():
                print(f"ERROR: OAuth2 credentials file not found: {_OAUTH2_CREDS_FILE}")
                print("Download it from GCP Console → APIs & Services → Credentials → OAuth 2.0 Client ID → Download JSON")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(_OAUTH2_CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_FILE.write_text(creds.to_json())
    return creds


def build_clients(sa_path: Path | None):
    """Return (sheets_service, drive_service).

    If sa_path is None, use OAuth2 user credentials (your own Google account).
    """
    if sa_path is None:
        creds = _get_oauth2_credentials()
    else:
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
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
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
    sd = trip["start_date"]
    if sd:
        date_str = sd.strftime("%Y-%m-%d") if hasattr(sd, "strftime") else str(sd)[:10]
    else:
        date_str = "0000-00-00"
    title = (trip["title"] or "Unnamed Trip")[:50]
    return f"{date_str} {trip['trip_uuid']} — {title}"


def create_spreadsheet(sheets_svc, drive_svc, folder_id: str, name: str) -> str:
    """Create an empty spreadsheet with the given name, move it to folder_id, return its ID."""
    body = {"properties": {"title": name}}
    resp = sheets_svc.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    spreadsheet_id = resp["spreadsheetId"]

    # Move from root ("My Drive") to target folder (supportsAllDrives for Shared Drive targets)
    file_meta = drive_svc.files().get(
        fileId=spreadsheet_id, fields="parents", supportsAllDrives=True
    ).execute()
    previous_parents = ",".join(file_meta.get("parents", []))
    drive_svc.files().update(
        fileId=spreadsheet_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields="id, parents",
        supportsAllDrives=True,
    ).execute()

    return spreadsheet_id


def populate_config_tab(sheets_svc, spreadsheet_id: str, trip: dict) -> None:
    """Fill the first (default) sheet with Config data and rename it to 'Config'."""
    sd, ed = trip["start_date"], trip["end_date"]
    start_date = (sd.strftime("%Y-%m-%d") if hasattr(sd, "strftime") else str(sd)[:10]) if sd else ""
    end_date = (ed.strftime("%Y-%m-%d") if hasattr(ed, "strftime") else str(ed)[:10]) if ed else ""

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


def add_pre_trip_tab(sheets_svc, spreadsheet_id: str) -> None:
    """Add a 'Pre-Trip' sheet with headers and example rows."""
    # Add the sheet
    resp = sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": "Pre-Trip"}}}]},
    ).execute()
    sheet_id = resp["replies"][0]["addSheet"]["properties"]["sheetId"]

    # Write header + example rows
    values = [PRE_TRIP_HEADER] + PRE_TRIP_EXAMPLE_ROWS
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Pre-Trip!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    _apply_header_formatting(sheets_svc, spreadsheet_id, sheet_id, num_cols=len(PRE_TRIP_HEADER))


def add_roteiro_tab(sheets_svc, spreadsheet_id: str) -> None:
    """Add a 'Roteiro' sheet with headers and one example row."""
    resp = sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": "Roteiro"}}}]},
    ).execute()
    sheet_id = resp["replies"][0]["addSheet"]["properties"]["sheetId"]

    values = [ROTEIRO_HEADER] + ROTEIRO_EXAMPLE_ROWS
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Roteiro!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    _apply_header_formatting(sheets_svc, spreadsheet_id, sheet_id, num_cols=len(ROTEIRO_HEADER))


async def main(folder_id: str, use_adc: bool) -> None:
    sa_path: Path | None
    if use_adc:
        sa_path = None
        print("Using Application Default Credentials (your Google account).")
    else:
        if not GCP_SERVICE_ACCOUNT_JSON:
            print("ERROR: GCP_SERVICE_ACCOUNT_JSON is not set in backend/.env")
            print("Tip: run with --use-adc to use your own Google account instead.")
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
    failed = 0
    urls = []

    for trip in trips:
        name = _sheet_name(trip)
        if name in existing_names:
            print(f"  ⏭  Skipped (already exists): {name}")
            skipped += 1
            continue

        print(f"  ✅ Creating: {name}...")
        spreadsheet_id = None
        try:
            spreadsheet_id = create_spreadsheet(sheets_svc, drive_svc, folder_id, name)
            populate_config_tab(sheets_svc, spreadsheet_id, trip)
            add_pre_trip_tab(sheets_svc, spreadsheet_id)
            add_roteiro_tab(sheets_svc, spreadsheet_id)
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            urls.append((name, url))
            created += 1
            time.sleep(12)  # stay well under 60 writes/min quota (each trip ~5 write calls)
        except Exception as exc:
            print(f"  ❌ Failed: {name} — {exc}")
            if spreadsheet_id:
                print(f"     Attempting to delete partially-created spreadsheet {spreadsheet_id}...")
                try:
                    drive_svc.files().delete(fileId=spreadsheet_id, supportsAllDrives=True).execute()
                    print("     Deleted. Re-run the script to retry this trip.")
                except Exception:
                    print(f"     Could not delete. Manually delete it from Google Drive before re-running:")
                    print(f"     https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            failed += 1

    print(f"\nDone: {created} created, {skipped} skipped, {failed} failed")
    for name, url in urls:
        print(f"  {name}\n    {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create trip content spreadsheets in Google Drive")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID")
    parser.add_argument(
        "--use-adc",
        action="store_true",
        help="Use Application Default Credentials (your own Google account) instead of service account. "
             "Run `gcloud auth application-default login` first.",
    )
    args = parser.parse_args()
    asyncio.run(main(args.folder_id, use_adc=args.use_adc))

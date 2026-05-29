"""
Create a single Google Sheets file with all trips' content in a Google Drive folder.

The spreadsheet has two tabs:
  - Pre-Trip  : pre-trip phases for all trips (trip_uuid as first column)
  - Roteiro   : day-by-day itinerary for all trips (trip_uuid as first column)

Usage (recommended — your own Google account):
  gcloud auth application-default login
  cd backend
  poetry run python scripts/create_trip_sheets.py --folder-id <GOOGLE_DRIVE_FOLDER_ID> --use-adc

  # Also delete old per-trip spreadsheets from the folder:
  poetry run python scripts/create_trip_sheets.py --folder-id <GOOGLE_DRIVE_FOLDER_ID> --use-adc --clean-old

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
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "Parrot Trips — Conteúdo de Viagens"

VIAGENS_HEADER = ["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim"]

FASES_HEADER = ["trip_uuid", "ordem", "fase", "titulo", "subtitulo", "icone", "descricao_curta", "descricao_completa"]

CHECKLIST_HEADER = ["trip_uuid", "fase", "ordem", "label", "obrigatorio"]

LINKS_HEADER = ["trip_uuid", "fase", "ordem", "label", "url"]

ROTEIRO_HEADER = [
    "trip_uuid", "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon",
    "dia_descricao_curta", "dia_descricao_completa",
    "atividade_nome", "atividade_tipo", "atividade_horario",
    "atividade_duracao_min", "atividade_descricao_curta",
    "atividade_info_pratica", "atividade_preco_brl",
]


def _fases_example_rows(trip_uuid: str) -> list[list[str]]:
    u = trip_uuid
    return [
        [u, "1", "visa",        "Visto",              "Requisitos de entrada para o Brasil",  "passport",  "Verifique os requisitos de visto para sua nacionalidade.", "Cidadãos americanos precisam de eVisa para o Brasil. Solicite com antecedência."],
        [u, "2", "vaccination", "Vacinas",             "Requisitos de saúde para viagem",      "syringe",   "Vacinas obrigatórias e recomendadas para o Brasil.",       "Febre amarela é fortemente recomendada. Consulte o CDC."],
        [u, "3", "packing",     "Como Arrumar a Mala", "O que levar na viagem",                "luggage",   "Dicas de bagagem para o Brasil.",                         "Clima quente e úmido. Leve roupas leves, protetor solar e adaptador (Tipo N)."],
        [u, "4", "documents",   "Documentos",          "Documentos de viagem necessários",     "file-text", "Todos os documentos essenciais para a viagem.",           "Mantenha cópias digitais e impressas. Passaporte com 6+ meses de validade."],
    ]


def _checklist_example_rows(trip_uuid: str) -> list[list[str]]:
    u = trip_uuid
    return [
        [u, "visa",        "1", "Verificar se sua nacionalidade requer visto",    "true"],
        [u, "visa",        "2", "Solicitar eVisa no portal oficial (se aplicável)", "true"],
        [u, "vaccination", "1", "Tomar vacina de febre amarela",                  "true"],
        [u, "vaccination", "2", "Obter carteira de vacinação internacional",       "false"],
        [u, "packing",     "1", "Roupas leves e respiráveis",                     "false"],
        [u, "packing",     "2", "Protetor solar FPS 50+",                         "false"],
        [u, "documents",   "1", "Passaporte válido (6+ meses de validade)",       "true"],
        [u, "documents",   "2", "Aprovação de visto impressa",                    "true"],
    ]


def _links_example_rows(trip_uuid: str) -> list[list[str]]:
    u = trip_uuid
    return [
        [u, "visa",        "1", "Portal eVisa Brasil", "https://www.gov.br/mre/pt-br/assuntos/portal-consular/vistos"],
        [u, "vaccination", "1", "CDC — Brasil",        "https://wwwnc.cdc.gov/travel/destinations/traveler/none/brazil"],
        [u, "packing",     "1", "Guia de tomadas do Brasil", "https://www.power-plugs-sockets.com/brazil/"],
        [u, "documents",   "1", "Guia de seguro viagem",     "https://www.gov.br/turismo/pt-br"],
    ]


def _roteiro_example_row(trip_uuid: str, trip: dict) -> list[str]:
    sd = trip["start_date"]
    date_str = (sd.strftime("%Y-%m-%d") if hasattr(sd, "strftime") else str(sd)[:10]) if sd else "YYYY-MM-DD"
    return [
        trip_uuid, "1", date_str, "Day 1 — Chegada", "Chegada", "plane-landing",
        "Transfer do aeroporto e check-in no hotel",
        "Bem-vindos! Você será recebido no aeroporto e levado ao hotel. À noite, Welcome Happy Hour.",
        "Transfer do Aeroporto", "logistics", "", "",
        "Recepção no aeroporto conforme formulário de pré-viagem.",
        "Procurar placa com o nome da Parrot Trips na área de desembarque.", "",
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

_TOKEN_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-token.json"
_OAUTH2_CREDS_FILE = Path(__file__).parent.parent / "secrets" / "gcp-oauth2-credentials.json"


async def fetch_trips(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        "SELECT trip_uuid, title, start_date, end_date FROM wetravel_trips ORDER BY start_date NULLS LAST"
    )
    return [dict(r) for r in rows]


def _get_oauth2_credentials() -> Credentials:
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
    if sa_path is None:
        creds = _get_oauth2_credentials()
    else:
        creds = service_account.Credentials.from_service_account_file(
            str(sa_path), scopes=SCOPES
        )
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return sheets, drive


def list_files_in_folder(drive, folder_id: str) -> list[dict]:
    """Return list of {id, name} for all files in the Drive folder."""
    files: list[dict] = []
    page_token = None
    while True:
        resp = (
            drive.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def create_spreadsheet(sheets_svc, drive_svc, folder_id: str, name: str) -> str:
    """Create an empty spreadsheet, move it to folder_id, return its ID."""
    body = {"properties": {"title": name}}
    resp = sheets_svc.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    spreadsheet_id = resp["spreadsheetId"]

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


def _get_first_sheet_id(sheets_svc, spreadsheet_id: str) -> int:
    meta = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return meta["sheets"][0]["properties"]["sheetId"]


def _apply_header_formatting(sheets_svc, spreadsheet_id: str, sheet_id: int, num_cols: int) -> None:
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


def populate_spreadsheet(sheets_svc, spreadsheet_id: str, trips: list[dict]) -> None:
    """Rename sheet 1 to Viagens, add Fases/Checklist/Links/Roteiro tabs, fill with example rows."""
    first_sheet_id = _get_first_sheet_id(sheets_svc, spreadsheet_id)

    # Rename first tab to Viagens
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": first_sheet_id, "title": "Viagens"},
                    "fields": "title",
                }
            }
        ]},
    ).execute()

    # Viagens tab — reference only
    sd_map = {}
    ed_map = {}
    for trip in trips:
        sd = trip["start_date"]
        ed = trip["end_date"]
        sd_map[trip["trip_uuid"]] = (sd.strftime("%Y-%m-%d") if hasattr(sd, "strftime") else str(sd)[:10]) if sd else ""
        ed_map[trip["trip_uuid"]] = (ed.strftime("%Y-%m-%d") if hasattr(ed, "strftime") else str(ed)[:10]) if ed else ""

    viagens_values = [VIAGENS_HEADER] + [
        [t["trip_uuid"], t["title"] or "", sd_map[t["trip_uuid"]], ed_map[t["trip_uuid"]]]
        for t in trips
    ]
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Viagens!A1",
        valueInputOption="RAW",
        body={"values": viagens_values},
    ).execute()
    _apply_header_formatting(sheets_svc, spreadsheet_id, first_sheet_id, num_cols=len(VIAGENS_HEADER))

    # Helper to add a new tab and write values
    def _add_tab(title: str, header: list[str], rows: list[list[str]]) -> None:
        resp = sheets_svc.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
        ).execute()
        sheet_id = resp["replies"][0]["addSheet"]["properties"]["sheetId"]
        sheets_svc.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{title}!A1",
            valueInputOption="RAW",
            body={"values": [header] + rows},
        ).execute()
        _apply_header_formatting(sheets_svc, spreadsheet_id, sheet_id, num_cols=len(header))

    fases_rows = []
    checklist_rows = []
    links_rows = []
    roteiro_rows = []
    for trip in trips:
        u = trip["trip_uuid"]
        fases_rows.extend(_fases_example_rows(u))
        checklist_rows.extend(_checklist_example_rows(u))
        links_rows.extend(_links_example_rows(u))
        roteiro_rows.append(_roteiro_example_row(u, trip))

    _add_tab("Fases",     FASES_HEADER,     fases_rows)
    _add_tab("Checklist", CHECKLIST_HEADER, checklist_rows)
    _add_tab("Links",     LINKS_HEADER,     links_rows)
    _add_tab("Roteiro",   ROTEIRO_HEADER,   roteiro_rows)


async def main(folder_id: str, use_adc: bool, clean_old: bool) -> None:
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
        print(f"  - {t['trip_uuid']} ({t['title']})")

    print("\nConnecting to Google APIs...")
    sheets_svc, drive_svc = build_clients(sa_path)

    print(f"Listing files in folder {folder_id}...")
    existing_files = list_files_in_folder(drive_svc, folder_id)
    existing_names = {f["name"]: f["id"] for f in existing_files}
    print(f"  Found {len(existing_files)} existing file(s)")

    # Delete old per-trip spreadsheets if requested
    if clean_old:
        old_files = [f for f in existing_files if f["name"] != SHEET_NAME]
        if old_files:
            print(f"\nDeleting {len(old_files)} old spreadsheet(s)...")
            for f in old_files:
                try:
                    drive_svc.files().delete(fileId=f["id"], supportsAllDrives=True).execute()
                    print(f"  🗑  Deleted: {f['name']}")
                    time.sleep(1)
                except Exception as exc:
                    print(f"  ⚠️  Could not delete '{f['name']}' ({exc}) — delete it manually from Drive")
        existing_names = {k: v for k, v in existing_names.items() if k == SHEET_NAME}

    # Create or skip the single spreadsheet
    if SHEET_NAME in existing_names:
        spreadsheet_id = existing_names[SHEET_NAME]
        print(f"\n⏭  Spreadsheet already exists — skipping creation.")
        print(f"   To repopulate it, delete it from Drive and re-run this script.")
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    else:
        print(f"\n✅ Creating: {SHEET_NAME}...")
        spreadsheet_id = create_spreadsheet(sheets_svc, drive_svc, folder_id, SHEET_NAME)
        populate_spreadsheet(sheets_svc, spreadsheet_id, trips)
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        print(f"   {url}")

    print(f"\nDone. Sheet ID: {spreadsheet_id}")
    print(f"Add to backend/.env:  TRIP_CONTENT_SHEET_ID={spreadsheet_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the single trip content spreadsheet in Google Drive")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID")
    parser.add_argument(
        "--use-adc",
        action="store_true",
        help="Use Application Default Credentials (your own Google account). "
             "Run `gcloud auth application-default login` first.",
    )
    parser.add_argument(
        "--clean-old",
        action="store_true",
        help="Delete existing per-trip spreadsheets from the folder before creating the new one.",
    )
    args = parser.parse_args()
    asyncio.run(main(args.folder_id, use_adc=args.use_adc, clean_old=args.clean_old))

# Create Trip Sheets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `backend/scripts/create_trip_sheets.py` — a script that reads all trips from the Supabase `wetravel_trips` table and creates a structured Google Sheets file per trip (with `Config`, `Pre-Trip`, and `Roteiro` tabs) inside a specified Google Drive folder, ready for the Parrot Trips team to fill in.

**Architecture:** The script uses `asyncpg` (already in the project) to query the database, and `google-api-python-client` with a GCP service account to create and format spreadsheets via the Google Sheets and Google Drive APIs. It is idempotent: if a file with the same name already exists in the target folder it is skipped. No web server, no FastAPI — a standalone CLI script following the same pattern as `gen_dev_users.py`.

**Tech Stack:** Python 3.12, asyncpg, google-api-python-client, google-auth, python-dotenv, Poetry

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `backend/scripts/create_trip_sheets.py` | Main CLI script |
| Modify | `backend/pyproject.toml` | Add google-* dependencies |
| Modify | `.gitignore` | Add `backend/secrets/` entry |

---

## Task 1: Add dependencies and gitignore

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `.gitignore`

- [ ] **Step 1: Add google-api packages to pyproject.toml**

Open `backend/pyproject.toml`. In `[tool.poetry.dependencies]`, add after the `"python-jose"` line:

```toml
google-auth = ">=2.0"
google-auth-httplib2 = ">=0.1"
google-api-python-client = ">=2.0"
```

- [ ] **Step 2: Install the new dependencies**

```bash
cd backend
poetry add google-auth google-auth-httplib2 google-api-python-client
```

Expected: Poetry resolves and installs the packages. `poetry.lock` is updated.

- [ ] **Step 3: Ensure `backend/secrets/` is gitignored**

Open `.gitignore` at the root of the repo. Find the `# Environment variables (secrets)` section and add:

```gitignore
# GCP service account key (never commit)
backend/secrets/
```

If the line already exists, skip this step.

- [ ] **Step 4: Create the secrets directory placeholder**

```bash
mkdir -p backend/secrets
touch backend/secrets/.gitkeep
```

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/poetry.lock .gitignore backend/secrets/.gitkeep
git commit -m "chore: add google-api-python-client deps and gitignore secrets dir"
```

---

## Task 2: Write the script skeleton and DB connection

**Files:**
- Create: `backend/scripts/create_trip_sheets.py`

This task creates the script file with the argument parser, `.env` loading, and the asyncpg DB query — without any Google API calls yet.

- [ ] **Step 1: Create the script file**

Create `backend/scripts/create_trip_sheets.py` with the following content:

```python
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
```

- [ ] **Step 2: Run the script to verify DB connection**

```bash
cd backend
poetry run python scripts/create_trip_sheets.py --folder-id test-folder-id
```

Expected output (exact trip names will differ):
```
Connecting to database...
Trips found: 7
  - 2026-11-20 k-latam-26 — K-LATAM 26 Brazil Trek
  - 2026-11-21 ysom-26 — YSOM Brazil Trek 26
  ...
(Google API integration not yet implemented)
```

If you see a DB connection error, check that `DATABASE_URL` is set in `backend/.env` and the Supabase pooler is reachable.

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/create_trip_sheets.py
git commit -m "feat: create_trip_sheets skeleton with DB query"
```

---

## Task 3: Build the Google Sheets API client helper

**Files:**
- Modify: `backend/scripts/create_trip_sheets.py`

This task adds the function that authenticates with the service account and returns the Sheets and Drive API clients. It also adds the function that lists existing files in the folder (for idempotency checks).

- [ ] **Step 1: Add imports and `build_clients` function**

At the top of `create_trip_sheets.py`, after the existing imports, add:

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
```

Add a new function after `_sheet_name`:

```python
def build_clients(sa_path: Path):
    """Return (sheets_service, drive_service) authenticated with the service account."""
    creds = service_account.Credentials.from_service_account_file(
        str(sa_path), scopes=SCOPES
    )
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return sheets, drive
```

- [ ] **Step 2: Add `list_existing_names` function**

Add after `build_clients`:

```python
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
```

- [ ] **Step 3: Wire into `main` to do a live folder listing**

Replace the `# Google API calls come in Task 3` comment in `main` with:

```python
    print("\nConnecting to Google APIs...")
    sheets_svc, drive_svc = build_clients(sa_path)

    print(f"Listing existing files in folder {folder_id}...")
    existing_names = list_existing_names(drive_svc, folder_id)
    print(f"  Found {len(existing_names)} existing file(s)")

    # Spreadsheet creation comes in Task 4
    print("\n(Spreadsheet creation not yet implemented)")
```

- [ ] **Step 4: Verify with a real folder ID (manual test)**

You need a real Google Drive folder ID and a valid service account file for this step. If the service account isn't set up yet, skip to Task 4 (creation logic) and come back.

If you have both:
```bash
cd backend
poetry run python scripts/create_trip_sheets.py --folder-id <YOUR_FOLDER_ID>
```

Expected:
```
Connecting to database...
Trips found: 7
  ...
Connecting to Google APIs...
Listing existing files in folder <YOUR_FOLDER_ID>...
  Found 0 existing file(s)
(Spreadsheet creation not yet implemented)
```

If you see `403 Forbidden`, the service account doesn't have access to the folder — share the folder with the service account email.

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/create_trip_sheets.py
git commit -m "feat: add google api client builder and folder listing"
```

---

## Task 4: Implement spreadsheet creation with Config tab

**Files:**
- Modify: `backend/scripts/create_trip_sheets.py`

This task adds the core creation logic: create a spreadsheet, move it to the target folder, and populate the `Config` tab.

- [ ] **Step 1: Add `create_spreadsheet` function**

Add after `list_existing_names`:

```python
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
```

- [ ] **Step 2: Add `populate_config_tab` function**

Add after `create_spreadsheet`:

```python
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
```

- [ ] **Step 3: Add `_apply_header_formatting` helper**

Add after `_get_first_sheet_id`:

```python
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
```

- [ ] **Step 4: Update `main` to call creation for one trip**

Replace the `# Spreadsheet creation comes in Task 4` comment with:

```python
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
```

- [ ] **Step 5: Run the script (requires real GCP credentials and folder)**

```bash
cd backend
poetry run python scripts/create_trip_sheets.py --folder-id <YOUR_FOLDER_ID>
```

Expected (first run):
```
Connecting to database...
Trips found: 7
  ...
Connecting to Google APIs...
Listing existing files in folder <ID>...
  Found 0 existing file(s)
  ✅ Creating: 2026-12-26 gsb-nye-brazil-2026 — GSB NYE Brazil Trek...
  ...
Done: 7 created, 0 skipped
  2026-12-26 gsb-nye-brazil-2026 — GSB NYE Brazil Trek
    https://docs.google.com/spreadsheets/d/...
```

Running again should show all 7 as skipped.

Open one spreadsheet URL and verify: `Config` tab exists, is renamed, has bold headers, row 1 is frozen, and the 4 data rows are correct.

- [ ] **Step 6: Commit**

```bash
git add backend/scripts/create_trip_sheets.py
git commit -m "feat: create spreadsheet and populate Config tab"
```

---

## Task 5: Add Pre-Trip tab with template rows

**Files:**
- Modify: `backend/scripts/create_trip_sheets.py`

- [ ] **Step 1: Define Pre-Trip template data constant**

Add this constant near the top of the file, after the `SCOPES` definition:

```python
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
```

- [ ] **Step 2: Add `add_pre_trip_tab` function**

Add after `_apply_header_formatting`:

```python
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
```

- [ ] **Step 3: Call `add_pre_trip_tab` in `main`**

Inside the `for trip in trips:` loop in `main`, after `populate_config_tab(...)`, add:

```python
        add_pre_trip_tab(sheets_svc, spreadsheet_id)
```

- [ ] **Step 4: Delete previously created test sheets and rerun**

Since the Config-only sheets from Task 4 are already in the folder, delete them manually from Google Drive (or use a different folder), then run again:

```bash
cd backend
poetry run python scripts/create_trip_sheets.py --folder-id <YOUR_FOLDER_ID>
```

Open one sheet and verify: `Pre-Trip` tab exists, has 5 bold header columns (fase, bloco, ordem, campo, valor), row 1 is frozen, and example rows for all 4 phases (visa, vaccination, packing, documents) are present.

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/create_trip_sheets.py
git commit -m "feat: add Pre-Trip tab with template rows"
```

---

## Task 6: Add Roteiro tab with template rows

**Files:**
- Modify: `backend/scripts/create_trip_sheets.py`

- [ ] **Step 1: Define Roteiro template data constant**

Add after `PRE_TRIP_EXAMPLE_ROWS`:

```python
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
```

- [ ] **Step 2: Add `add_roteiro_tab` function**

Add after `add_pre_trip_tab`:

```python
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
```

- [ ] **Step 3: Call `add_roteiro_tab` in `main`**

Inside the `for trip in trips:` loop, after `add_pre_trip_tab(...)`, add:

```python
        add_roteiro_tab(sheets_svc, spreadsheet_id)
```

- [ ] **Step 4: Delete test sheets, rerun, and verify**

```bash
cd backend
poetry run python scripts/create_trip_sheets.py --folder-id <YOUR_FOLDER_ID>
```

Open one sheet and verify:
- 3 tabs: `Config`, `Pre-Trip`, `Roteiro`
- `Roteiro` tab: 14 bold header columns, row 1 frozen, 1 example row
- Run again → all 7 skipped

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/create_trip_sheets.py
git commit -m "feat: add Roteiro tab with template rows"
```

---

## Task 7: Final polish — .env.example and README note

**Files:**
- Modify: `backend/.env.example`

The project uses `.env.example` as documentation for required environment variables.

- [ ] **Step 1: Add GCP variable to `.env.example`**

Open `backend/.env.example`. Add at the end:

```bash
# GCP service account key for Google Sheets/Drive API
# Download from GCP Console → IAM → Service Accounts → Keys → Add Key → JSON
# Save to backend/secrets/gcp-service-account.json (gitignored)
GCP_SERVICE_ACCOUNT_JSON=secrets/gcp-service-account.json
```

- [ ] **Step 2: Verify the full end-to-end flow one more time**

```bash
cd backend
poetry run python scripts/create_trip_sheets.py --folder-id <YOUR_FOLDER_ID>
```

Confirm:
1. All 7 trips create spreadsheets on first run
2. Re-running skips all 7 (idempotent)
3. Each spreadsheet has `Config`, `Pre-Trip`, `Roteiro` tabs
4. `Config` has correct `trip_uuid`, `trip_title`, `start_date`, `end_date` from the database
5. `Pre-Trip` has all 4 phases (visa, vaccination, packing, documents) with example rows
6. `Roteiro` has 14-column header and 1 example row

- [ ] **Step 3: Commit**

```bash
git add backend/.env.example
git commit -m "chore: document GCP_SERVICE_ACCOUNT_JSON in .env.example"
```

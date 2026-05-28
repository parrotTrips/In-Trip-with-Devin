# Import Trip Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `backend/scripts/import_trip_content.py` — a CLI script that reads a filled Google Sheets spreadsheet for a single trip and upserts its content into Supabase (`trip_phases`, `trip_phase_checklist_items`, `trip_phase_links`, `trip_activities`).

**Architecture:** The script reads three tabs (`Config`, `Pre-Trip`, `Roteiro`) from a spreadsheet identified by `--sheet-id`, parses them into typed Python dataclasses, then performs a full replace for the trip: delete all existing phases and dependents for the trip UUID, then insert fresh rows inside a single transaction. This is simpler and safer than row-level upsert for this scale of data.

**Tech Stack:** Python 3.12+, asyncpg (direct SQL — same pattern as `seed_placeholder_trip.py`), google-api-python-client + google-auth-oauthlib (same OAuth2 flow as `create_trip_sheets.py`), python-dotenv, pytest for unit tests.

---

## File Structure

| File | Role |
|---|---|
| `backend/scripts/import_trip_content.py` | Main CLI script (create) |
| `backend/tests/scripts/test_import_trip_content.py` | Unit tests for parse functions (create) |

No app files are touched — this is a standalone script with no FastAPI dependency.

---

### Task 1: Scaffold the script with CLI and Sheets reader

**Files:**
- Create: `backend/scripts/import_trip_content.py`

- [ ] **Step 1: Create the script file**

```python
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
```

- [ ] **Step 2: Add OAuth2 helper (reuse pattern from create_trip_sheets.py)**

Append to the file:

```python
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
```

- [ ] **Step 3: Verify the file runs without import errors**

```bash
cd backend
poetry run python scripts/import_trip_content.py --help
```

Expected output:
```
usage: import_trip_content.py [-h] --sheet-id SHEET_ID
...
```

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/import_trip_content.py
git commit -m "feat: scaffold import_trip_content.py with CLI and Sheets reader"
```

---

### Task 2: Dataclasses and parse_config_tab

**Files:**
- Modify: `backend/scripts/import_trip_content.py`
- Create: `backend/tests/scripts/__init__.py`
- Create: `backend/tests/scripts/test_import_trip_content.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/scripts/__init__.py` (empty).

Create `backend/tests/scripts/test_import_trip_content.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_trip_content import (
    TripConfig,
    PreTripPhase,
    ChecklistItem,
    PhaseLink,
    InTripDay,
    Activity,
    parse_config_tab,
    parse_pre_trip_tab,
    parse_roteiro_tab,
)


def test_parse_config_tab_basic():
    rows = [
        ["chave", "valor"],
        ["trip_uuid", "gsb-nye-2026"],
        ["trip_title", "GSB NYE Brazil Trek"],
        ["start_date", "2026-12-26"],
        ["end_date", "2027-01-04"],
    ]
    cfg = parse_config_tab(rows)
    assert cfg.trip_uuid == "gsb-nye-2026"
    assert cfg.trip_title == "GSB NYE Brazil Trek"
    assert cfg.start_date == "2026-12-26"


def test_parse_config_tab_missing_uuid_raises():
    rows = [["chave", "valor"], ["trip_title", "Something"]]
    try:
        parse_config_tab(rows)
        assert False, "should have raised"
    except ValueError as e:
        assert "trip_uuid" in str(e)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py::test_parse_config_tab_basic -v
```

Expected: FAIL with `ImportError` or `ModuleNotFoundError`.

- [ ] **Step 3: Add dataclasses and parse_config_tab to the script**

Append to `backend/scripts/import_trip_content.py`:

```python
# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class TripConfig:
    trip_uuid: str
    trip_title: str
    start_date: str  # YYYY-MM-DD string — used to compute starts_at for days


@dataclass
class ChecklistItem:
    label: str
    is_required: bool
    sort_order: int


@dataclass
class PhaseLink:
    label: str
    url: str
    sort_order: int


@dataclass
class PreTripPhase:
    fase: str           # visa | vaccination | packing | documents
    title: str
    subtitle: str
    icon: str
    short_description: str
    detailed_description: str
    checklist: list[ChecklistItem] = field(default_factory=list)
    links: list[PhaseLink] = field(default_factory=list)


@dataclass
class Activity:
    name: str
    activity_type: str   # included | optional | suggested | logistics
    horario: str         # raw string e.g. "10:00" — stored in short_description context
    duration_minutes: int | None
    short_description: str
    practical_info: str
    amount_brl: float | None
    sort_order: int


@dataclass
class InTripDay:
    dia: int             # day number (1-based)
    data: str            # YYYY-MM-DD
    title: str
    subtitle: str
    icon: str
    short_description: str
    detailed_description: str
    activities: list[Activity] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_config_tab(rows: list[list[str]]) -> TripConfig:
    """Parse Config tab rows into TripConfig. First row is header."""
    data: dict[str, str] = {}
    for row in rows[1:]:  # skip header
        if len(row) >= 2:
            data[row[0].strip()] = row[1].strip()
    if not data.get("trip_uuid"):
        raise ValueError("Config tab is missing required key: trip_uuid")
    return TripConfig(
        trip_uuid=data["trip_uuid"],
        trip_title=data.get("trip_title", ""),
        start_date=data.get("start_date", ""),
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py::test_parse_config_tab_basic tests/scripts/test_import_trip_content.py::test_parse_config_tab_missing_uuid_raises -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/import_trip_content.py backend/tests/scripts/
git commit -m "feat: add dataclasses and parse_config_tab"
```

---

### Task 3: parse_pre_trip_tab

**Files:**
- Modify: `backend/scripts/import_trip_content.py`
- Modify: `backend/tests/scripts/test_import_trip_content.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/scripts/test_import_trip_content.py`:

```python
def test_parse_pre_trip_tab_visa():
    rows = [
        ["fase", "bloco", "ordem", "campo", "valor"],
        # header block
        ["visa", "header", "1", "title", "Visto"],
        ["visa", "header", "1", "subtitle", "Requisitos de entrada"],
        ["visa", "header", "1", "icon", "passport"],
        ["visa", "header", "1", "short_description", "Verifique o visto."],
        ["visa", "header", "1", "detailed_description", "Cidadãos americanos precisam de eVisa."],
        # checklist
        ["visa", "checklist", "1", "label", "Verificar necessidade de visto"],
        ["visa", "checklist", "1", "is_required", "true"],
        ["visa", "checklist", "2", "label", "Solicitar eVisa"],
        ["visa", "checklist", "2", "is_required", "false"],
        # link
        ["visa", "link", "1", "label", "Portal eVisa"],
        ["visa", "link", "1", "url", "https://www.gov.br"],
    ]
    phases = parse_pre_trip_tab(rows)
    assert len(phases) == 1
    visa = phases[0]
    assert visa.fase == "visa"
    assert visa.title == "Visto"
    assert visa.icon == "passport"
    assert len(visa.checklist) == 2
    assert visa.checklist[0].label == "Verificar necessidade de visto"
    assert visa.checklist[0].is_required is True
    assert visa.checklist[1].is_required is False
    assert len(visa.links) == 1
    assert visa.links[0].url == "https://www.gov.br"


def test_parse_pre_trip_tab_skips_empty_rows():
    rows = [
        ["fase", "bloco", "ordem", "campo", "valor"],
        ["visa", "header", "1", "title", "Visto"],
        ["visa", "header", "1", "subtitle", "Req"],
        ["visa", "header", "1", "icon", "passport"],
        ["visa", "header", "1", "short_description", "Check."],
        ["visa", "header", "1", "detailed_description", "Details."],
        [],  # empty row — must be skipped
        ["", "", "", "", ""],  # blank row — must be skipped
    ]
    phases = parse_pre_trip_tab(rows)
    assert len(phases) == 1
    assert phases[0].checklist == []
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py::test_parse_pre_trip_tab_visa -v
```

Expected: FAIL with `ImportError` (function not defined yet).

- [ ] **Step 3: Implement parse_pre_trip_tab**

Append to `backend/scripts/import_trip_content.py`:

```python
def parse_pre_trip_tab(rows: list[list[str]]) -> list[PreTripPhase]:
    """Parse Pre-Trip tab. Returns one PreTripPhase per distinct fase value."""
    phases: dict[str, PreTripPhase] = {}
    checklist_by_fase: dict[str, dict[int, dict[str, str]]] = {}
    links_by_fase: dict[str, dict[int, dict[str, str]]] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 5:
            continue
        fase, bloco, ordem_str, campo, valor = (row[i].strip() if i < len(row) else "" for i in range(5))
        if not fase or not bloco or not campo:
            continue

        try:
            ordem = int(ordem_str)
        except ValueError:
            continue

        if bloco == "header":
            if fase not in phases:
                phases[fase] = PreTripPhase(
                    fase=fase, title="", subtitle="", icon="",
                    short_description="", detailed_description="",
                )
            p = phases[fase]
            if campo == "title":
                p.title = valor
            elif campo == "subtitle":
                p.subtitle = valor
            elif campo == "icon":
                p.icon = valor
            elif campo == "short_description":
                p.short_description = valor
            elif campo == "detailed_description":
                p.detailed_description = valor

        elif bloco == "checklist":
            if fase not in checklist_by_fase:
                checklist_by_fase[fase] = {}
            if ordem not in checklist_by_fase[fase]:
                checklist_by_fase[fase][ordem] = {}
            checklist_by_fase[fase][ordem][campo] = valor

        elif bloco == "link":
            if fase not in links_by_fase:
                links_by_fase[fase] = {}
            if ordem not in links_by_fase[fase]:
                links_by_fase[fase][ordem] = {}
            links_by_fase[fase][ordem][campo] = valor

    # Assemble checklist and links into phases
    for fase, phase in phases.items():
        for sort_order, fields in sorted(checklist_by_fase.get(fase, {}).items()):
            label = fields.get("label", "")
            if not label:
                continue
            is_required = fields.get("is_required", "false").lower() == "true"
            phase.checklist.append(ChecklistItem(label=label, is_required=is_required, sort_order=sort_order - 1))

        for sort_order, fields in sorted(links_by_fase.get(fase, {}).items()):
            label = fields.get("label", "")
            url = fields.get("url", "")
            if not label or not url:
                continue
            phase.links.append(PhaseLink(label=label, url=url, sort_order=sort_order - 1))

    return list(phases.values())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py::test_parse_pre_trip_tab_visa tests/scripts/test_import_trip_content.py::test_parse_pre_trip_tab_skips_empty_rows -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/import_trip_content.py backend/tests/scripts/test_import_trip_content.py
git commit -m "feat: implement parse_pre_trip_tab with tests"
```

---

### Task 4: parse_roteiro_tab

**Files:**
- Modify: `backend/scripts/import_trip_content.py`
- Modify: `backend/tests/scripts/test_import_trip_content.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/scripts/test_import_trip_content.py`:

```python
def test_parse_roteiro_tab_basic():
    rows = [
        [
            "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon",
            "dia_descricao_curta", "dia_descricao_completa",
            "atividade_nome", "atividade_tipo", "atividade_horario",
            "atividade_duracao_min", "atividade_descricao_curta",
            "atividade_info_pratica", "atividade_preco_brl",
        ],
        [
            "1", "2026-12-26", "Day 1 — Dec 26", "Chegada", "plane-landing",
            "Transfer e check-in", "Bem-vindos ao Rio!",
            "Transfer do Aeroporto", "logistics", "14:00",
            "120", "Recepção no aeroporto", "Procurar placa Parrot Trips", "",
        ],
        [
            "1", "2026-12-26", "Day 1 — Dec 26", "Chegada", "plane-landing",
            "Transfer e check-in", "Bem-vindos ao Rio!",
            "Welcome Happy Hour", "included", "18:00",
            "240", "Open bar na praia", "", "",
        ],
        [
            "2", "2026-12-27", "Day 2 — Dec 27", "Passeio", "sun",
            "Dia de praia", "Curta o Rio!",
            "Praia de Ipanema", "suggested", "09:00",
            "", "Aproveite a praia", "", "",
        ],
    ]
    days = parse_roteiro_tab(rows)
    assert len(days) == 2

    day1 = days[0]
    assert day1.dia == 1
    assert day1.data == "2026-12-26"
    assert day1.title == "Day 1 — Dec 26"
    assert len(day1.activities) == 2
    assert day1.activities[0].name == "Transfer do Aeroporto"
    assert day1.activities[0].activity_type == "logistics"
    assert day1.activities[0].duration_minutes == 120
    assert day1.activities[1].name == "Welcome Happy Hour"

    day2 = days[1]
    assert day2.dia == 2
    assert len(day2.activities) == 1
    assert day2.activities[0].duration_minutes is None


def test_parse_roteiro_tab_optional_price():
    rows = [
        [
            "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon",
            "dia_descricao_curta", "dia_descricao_completa",
            "atividade_nome", "atividade_tipo", "atividade_horario",
            "atividade_duracao_min", "atividade_descricao_curta",
            "atividade_info_pratica", "atividade_preco_brl",
        ],
        [
            "1", "2026-12-26", "Day 1", "", "sun",
            "desc", "",
            "Bike Tour", "optional", "09:00",
            "180", "Tour de bicicleta", "", "150",
        ],
    ]
    days = parse_roteiro_tab(rows)
    assert days[0].activities[0].amount_brl == 150.0
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py::test_parse_roteiro_tab_basic -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement parse_roteiro_tab**

Append to `backend/scripts/import_trip_content.py`:

```python
_ROTEIRO_COLS = [
    "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon",
    "dia_descricao_curta", "dia_descricao_completa",
    "atividade_nome", "atividade_tipo", "atividade_horario",
    "atividade_duracao_min", "atividade_descricao_curta",
    "atividade_info_pratica", "atividade_preco_brl",
]


def _cell(row: list[str], col: str) -> str:
    try:
        idx = _ROTEIRO_COLS.index(col)
        return row[idx].strip() if idx < len(row) else ""
    except ValueError:
        return ""


def parse_roteiro_tab(rows: list[list[str]]) -> list[InTripDay]:
    """Parse Roteiro tab. Returns one InTripDay per distinct dia value, preserving order."""
    days: dict[int, InTripDay] = {}
    activity_counters: dict[int, int] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 8:
            continue
        dia_str = _cell(row, "dia")
        if not dia_str.isdigit():
            continue
        dia = int(dia_str)

        if dia not in days:
            days[dia] = InTripDay(
                dia=dia,
                data=_cell(row, "data"),
                title=_cell(row, "dia_titulo"),
                subtitle=_cell(row, "dia_subtitulo"),
                icon=_cell(row, "dia_icon"),
                short_description=_cell(row, "dia_descricao_curta"),
                detailed_description=_cell(row, "dia_descricao_completa"),
            )
            activity_counters[dia] = 0

        atividade_nome = _cell(row, "atividade_nome")
        if not atividade_nome:
            continue

        dur_str = _cell(row, "atividade_duracao_min")
        duration_minutes: int | None = int(dur_str) if dur_str.isdigit() else None

        preco_str = _cell(row, "atividade_preco_brl")
        amount_brl: float | None = None
        try:
            if preco_str:
                amount_brl = float(preco_str)
        except ValueError:
            pass

        days[dia].activities.append(Activity(
            name=atividade_nome,
            activity_type=_cell(row, "atividade_tipo"),
            horario=_cell(row, "atividade_horario"),
            duration_minutes=duration_minutes,
            short_description=_cell(row, "atividade_descricao_curta"),
            practical_info=_cell(row, "atividade_info_pratica"),
            amount_brl=amount_brl,
            sort_order=activity_counters[dia],
        ))
        activity_counters[dia] += 1

    return list(days.values())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py::test_parse_roteiro_tab_basic tests/scripts/test_import_trip_content.py::test_parse_roteiro_tab_optional_price -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Run all tests so far**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py -v
```

Expected: all 6 tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/scripts/import_trip_content.py backend/tests/scripts/test_import_trip_content.py
git commit -m "feat: implement parse_roteiro_tab with tests"
```

---

### Task 5: Database writer (upsert to Supabase)

**Files:**
- Modify: `backend/scripts/import_trip_content.py`

The writer deletes all existing phases for the trip and re-inserts everything in a single transaction. This is safe because `trip_travelers` and `traveler_checklist_progress` reference phases by ID — deleting phases will cascade via FK or fail loudly if travelers have progress. To handle this: delete `traveler_checklist_progress` and `traveler_phase_progress` for the trip's travelers first, then phases.

- [ ] **Step 1: Add the write_to_db function**

Append to `backend/scripts/import_trip_content.py`:

```python
async def write_to_db(
    conn: asyncpg.Connection,
    config: TripConfig,
    pre_trip_phases: list[PreTripPhase],
    in_trip_days: list[InTripDay],
) -> None:
    """Delete all existing phase data for the trip and insert fresh rows. Runs in a transaction."""
    trip_uuid = config.trip_uuid

    async with conn.transaction():
        # 1. Delete traveler progress that references checklist items and phases for this trip
        phase_ids = await conn.fetch(
            "SELECT id FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if phase_ids:
            ids = [str(r["id"]) for r in phase_ids]
            traveler_rows = await conn.fetch(
                "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
            )
            if traveler_rows:
                tt_ids = [str(r["id"]) for r in traveler_rows]
                await conn.execute(
                    "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
                await conn.execute(
                    "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
            await conn.execute(
                "DELETE FROM trip_activities WHERE trip_phase_id = ANY($1::uuid[])", ids
            )
            await conn.execute(
                "DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = ANY($1::uuid[])", ids
            )
            await conn.execute(
                "DELETE FROM trip_phase_links WHERE trip_phase_id = ANY($1::uuid[])", ids
            )
            await conn.execute(
                "DELETE FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
            )

        # 2. Insert pre-trip phases
        FIXED_PHASE_ORDER = ["visa", "vaccination", "packing", "documents"]
        phase_map = {p.fase: p for p in pre_trip_phases}
        sort_order = 0
        for fase_key in FIXED_PHASE_ORDER:
            phase = phase_map.get(fase_key)
            if not phase:
                continue
            phase_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO trip_phases
                    (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                     short_description, detailed_description, sort_order,
                     is_locked_by_default, is_visible, created_at, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,now(),now())
                """,
                phase_id, trip_uuid, "pre-trip", phase.title, phase.subtitle,
                phase.icon, phase.short_description, phase.detailed_description,
                sort_order, False, True,
            )
            sort_order += 1
            for item in phase.checklist:
                await conn.execute(
                    """
                    INSERT INTO trip_phase_checklist_items
                        (id, trip_phase_id, label, sort_order, is_required, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,now(),now())
                    """,
                    str(uuid.uuid4()), phase_id, item.label, item.sort_order, item.is_required,
                )
            for link in phase.links:
                await conn.execute(
                    """
                    INSERT INTO trip_phase_links
                        (id, trip_phase_id, label, url, sort_order, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,now(),now())
                    """,
                    str(uuid.uuid4()), phase_id, link.label, link.url, link.sort_order,
                )

        # 3. Insert in-trip days
        for day in in_trip_days:
            phase_id = str(uuid.uuid4())
            try:
                starts_at = datetime.strptime(day.data, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                starts_at = None
            await conn.execute(
                """
                INSERT INTO trip_phases
                    (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                     short_description, detailed_description, sort_order,
                     starts_at, is_locked_by_default, is_visible, created_at, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,now(),now())
                """,
                phase_id, trip_uuid, "in-trip", day.title, day.subtitle,
                day.icon, day.short_description, day.detailed_description,
                sort_order, starts_at, False, True,
            )
            sort_order += 1
            for act in day.activities:
                await conn.execute(
                    """
                    INSERT INTO trip_activities
                        (id, trip_phase_id, name, activity_type,
                         duration_minutes, short_description, practical_info,
                         amount_brl, sort_order, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,now(),now())
                    """,
                    str(uuid.uuid4()), phase_id, act.name, act.activity_type,
                    act.duration_minutes, act.short_description,
                    act.practical_info or None, act.amount_brl, act.sort_order,
                )
```

- [ ] **Step 2: Verify the file has no syntax errors**

```bash
cd backend
poetry run python -c "import scripts.import_trip_content"
```

Expected: no output (clean import).

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/import_trip_content.py
git commit -m "feat: add write_to_db — deletes existing phases and inserts fresh data"
```

---

### Task 6: main() function and end-to-end wiring

**Files:**
- Modify: `backend/scripts/import_trip_content.py`

- [ ] **Step 1: Add main() and entry point**

Append to `backend/scripts/import_trip_content.py`:

```python
async def main(sheet_id: str) -> None:
    print("Connecting to Google Sheets...")
    sheets_svc = build_sheets_client()

    print("Reading Config tab...")
    config_rows = read_tab(sheets_svc, sheet_id, "Config")
    config = parse_config_tab(config_rows)
    print(f"  trip_uuid : {config.trip_uuid}")
    print(f"  trip_title: {config.trip_title}")
    print(f"  start_date: {config.start_date}")

    print("Reading Pre-Trip tab...")
    pre_trip_rows = read_tab(sheets_svc, sheet_id, "Pre-Trip")
    pre_trip_phases = parse_pre_trip_tab(pre_trip_rows)
    print(f"  {len(pre_trip_phases)} pre-trip phase(s): {[p.fase for p in pre_trip_phases]}")

    print("Reading Roteiro tab...")
    roteiro_rows = read_tab(sheets_svc, sheet_id, "Roteiro")
    in_trip_days = parse_roteiro_tab(roteiro_rows)
    total_activities = sum(len(d.activities) for d in in_trip_days)
    print(f"  {len(in_trip_days)} day(s), {total_activities} activit(ies)")

    print("\nConnecting to database...")
    conn = await asyncpg.connect(PG_URL)
    try:
        await write_to_db(conn, config, pre_trip_phases, in_trip_days)
    finally:
        await conn.close()

    total_checklist = sum(len(p.checklist) for p in pre_trip_phases)
    total_links = sum(len(p.links) for p in pre_trip_phases)
    print("\n✅ Import complete!")
    print(f"   Pre-trip phases : {len(pre_trip_phases)}")
    print(f"   Checklist items : {total_checklist}")
    print(f"   Links           : {total_links}")
    print(f"   In-trip days    : {len(in_trip_days)}")
    print(f"   Activities      : {total_activities}")


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
    asyncio.run(main(args.sheet_id))
```

- [ ] **Step 2: Test --help works**

```bash
cd backend
poetry run python scripts/import_trip_content.py --help
```

Expected output includes:
```
usage: import_trip_content.py [-h] --sheet-id SHEET_ID
...
  --sheet-id SHEET_ID  Google Sheets spreadsheet ID
```

- [ ] **Step 3: Run all unit tests**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py -v
```

Expected: all 6 PASSED.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/import_trip_content.py
git commit -m "feat: add main() and wire up full import pipeline"
```

---

### Task 7: Live smoke test against GSB NYE spreadsheet

This task runs the script against the real spreadsheet and verifies data appears in the app. No automated test — this is a manual smoke test.

**The GSB NYE Brazil Trek spreadsheet ID** is found in the URL printed when `create_trip_sheets.py` was run. Look for it in the output from before:
```
2026-12-26 2425416057 — GSB NYE Brazil Trek
  https://docs.google.com/spreadsheets/d/1wkc7rtWKkisLrddYJqmY9sLbNao2TEc7pjPXojXkG9M
```
Sheet ID: `1wkc7rtWKkisLrddYJqmY9sLbNao2TEc7pjPXojXkG9M`

- [ ] **Step 1: Fill in at least Day 1 and the visa phase in the GSB sheet**

Open the spreadsheet, fill in a few rows of Pre-Trip (visa section) and at least one day of Roteiro with real data. At minimum:

Pre-Trip rows:
```
visa | header | 1 | title           | Visto
visa | header | 1 | subtitle        | Requisitos para o Brasil
visa | header | 1 | icon            | passport
visa | header | 1 | short_description | Verifique os requisitos de visto.
visa | header | 1 | detailed_description | Cidadãos americanos precisam de eVisa.
visa | checklist | 1 | label        | Verificar se precisa de visto
visa | checklist | 1 | is_required  | true
visa | link    | 1 | label          | Portal eVisa Brasil
visa | link    | 1 | url            | https://www.gov.br/mre/pt-br/assuntos/portal-consular/vistos
```

Roteiro row (Day 1):
```
1 | 2026-12-26 | Day 1 — Dec 26 | Chegada | plane-landing | Transfer e check-in | Bem-vindos! | Transfer do Aeroporto | logistics | 14:00 | 120 | Recepção no aeroporto | Procurar placa Parrot Trips |
```

- [ ] **Step 2: Run the import script**

```bash
cd backend
poetry run python scripts/import_trip_content.py --sheet-id 1wkc7rtWKkisLrddYJqmY9sLbNao2TEc7pjPXojXkG9M
```

Expected:
```
Connecting to Google Sheets...
Reading Config tab...
  trip_uuid : 2425416057
  trip_title: GSB NYE Brazil Trek
  ...
Reading Pre-Trip tab...
  1 pre-trip phase(s): ['visa']
Reading Roteiro tab...
  1 day(s), 1 activit(ies)

Connecting to database...

✅ Import complete!
   Pre-trip phases : 1
   Checklist items : 1
   Links           : 1
   In-trip days    : 1
   Activities      : 1
```

- [ ] **Step 3: Verify in the app**

Open the Parrot Trips app logged in as a GSB traveler. Navigate to the Pre-Trip section — you should see the Visa phase with the content from the spreadsheet.

- [ ] **Step 4: Re-run the script (idempotency check)**

Run the same command again without changing the spreadsheet:

```bash
poetry run python scripts/import_trip_content.py --sheet-id 1wkc7rtWKkisLrddYJqmY9sLbNao2TEc7pjPXojXkG9M
```

Expected: same output as before, no errors, database state unchanged.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: complete import_trip_content.py — reads Sheets, writes to Supabase"
```

---

## Post-implementation notes

- To import another trip: `poetry run python scripts/import_trip_content.py --sheet-id <ID>`
- The Sheet ID is in the URL: `https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`
- Re-running always replaces all phase data for the trip. Traveler checklist progress is deleted on reimport (acceptable for pre-launch; add a backup step later if needed).
- Horário (time) is stored as a string in the `atividade_horario` column but `trip_activities.starts_at` is a `TIMESTAMPTZ`. The script does **not** populate `starts_at` for activities — it only fills `short_description`, `duration_minutes`, `practical_info`, and `amount_brl`. If `starts_at` needs to be set for activities, a future enhancement can combine `day.data` + `act.horario` into a full datetime.

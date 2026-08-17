# Casamento GaRapha Content Sheets Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Populate the wedding trip content from `20260806 - Data Request Casamento GaRapha.md` into Google Sheets and import it into Supabase while keeping `CASAMENTO-GARAPHA-2026` in `pre-trip`.

**Architecture:** Add a focused idempotent script that converts the approved wedding content into the existing Trip Content and Staff Content sheet tabs. Reuse the existing import scripts/services to move those rows into Supabase, adding only a small orchestration wrapper if needed.

**Tech Stack:** Python 3.12, asyncpg, Google Sheets API, pytest, existing backend scripts.

---

### Task 1: Add Sheet Row Builder Tests

**Files:**
- Create: `backend/tests/scripts/test_seed_casamento_garapha_content.py`
- Create: `backend/scripts/seed_casamento_garapha_content.py`

**Step 1: Write failing tests**

Add tests for:

- `TRIP_UUID == "CASAMENTO-GARAPHA-2026"`.
- `build_sheet_rows()["content"]["Fases"]` returns four pre-trip rows.
- `build_sheet_rows()["content"]["Checklist"]` includes travel logistics, packing, wellbeing, and wedding information checklist items.
- `build_sheet_rows()["content"]["Roteiro"]` returns four activity rows across three days.
- `build_sheet_rows()["content"]["FAQ"]` returns the three filled FAQ rows.
- `build_sheet_rows()["content"]["Recomendacoes"]` skips placeholder rows and includes real recommendation rows.
- `build_sheet_rows()["content"]["Emergency Contacts"]` contains Marine Carneiro.
- `build_sheet_rows()["staff"]["Contatos"]` contains Marine Carneiro.

**Step 2: Run tests and verify failure**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/scripts/test_seed_casamento_garapha_content.py -q
```

Expected: FAIL because `scripts.seed_casamento_garapha_content` does not exist yet.

### Task 2: Implement Wedding Content Constants

**Files:**
- Modify: `backend/scripts/seed_casamento_garapha_content.py`
- Test: `backend/tests/scripts/test_seed_casamento_garapha_content.py`

**Step 1: Add constants**

Define:

- `TRIP_UUID = "CASAMENTO-GARAPHA-2026"`
- `TRIP_CONTENT_SHEET_ID` and `STAFF_CONTENT_SHEET_ID` from `backend/.env`, falling back to the known IDs used by the existing scripts only if env vars are absent.
- headers compatible with `backend/scripts/seed_parrot_test_travelers.py` for:
  - `Viagens`
  - `Emergency Contacts`
  - `Recomendacoes`
  - `Fases`
  - `Checklist`
  - `Links`
  - `Roteiro`
  - `FAQ`
  - `Contatos`

**Step 2: Add `build_sheet_rows()`**

Return:

```python
{
    "content": {
        "Viagens": [...],
        "Emergency Contacts": [...],
        "Recomendacoes": [...],
        "Fases": [...],
        "Checklist": [...],
        "Links": [...],
        "Roteiro": [...],
        "FAQ": [...],
    },
    "staff": {
        "Contatos": [...],
    },
}
```

Use these pre-trip phase keys:

- `logistica_de_viagem`
- `preparando_as_malas`
- `cuidados_e_bem_estar`
- `informacoes_do_casamento`

Use these in-trip days:

- Day 1, `2026-09-04`: `Jantar de Boas Vindas`
- Day 2, `2026-09-05`: `Passeio de Jangada`; `Festa Pre Wedding`
- Day 3, `2026-09-06`: `Casamento`

**Step 3: Run tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/scripts/test_seed_casamento_garapha_content.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add backend/scripts/seed_casamento_garapha_content.py backend/tests/scripts/test_seed_casamento_garapha_content.py
git commit -m "feat: build casamento garapha content sheet rows"
```

### Task 3: Add Idempotent Sheet Writer

**Files:**
- Modify: `backend/scripts/seed_casamento_garapha_content.py`
- Test: `backend/tests/scripts/test_seed_casamento_garapha_content.py`

**Step 1: Add unit tests for row replacement**

Cover:

- existing rows for other trips are preserved;
- existing rows for `CASAMENTO-GARAPHA-2026` are removed before appending fresh rows;
- missing tabs use the managed header.

**Step 2: Implement helpers**

Implement or adapt from `backend/scripts/seed_parrot_test_travelers.py`:

- `normalize_sheet_values(rows)`
- `row_matches_trip_uuid(row, header, trip_uuid=TRIP_UUID)`
- `merge_trip_rows(existing_rows, header, new_rows, trip_uuid=TRIP_UUID)`
- `ensure_tab(sheets, spreadsheet_id, tab)`
- `replace_trip_rows(sheets, spreadsheet_id, tab, new_rows)`
- `update_sheets(sheets, rows)`

Keep the write range to `A:Z` so current headers fit.

**Step 3: Add CLI**

Support:

```bash
cd backend && .venv/bin/python scripts/seed_casamento_garapha_content.py
cd backend && .venv/bin/python scripts/seed_casamento_garapha_content.py --execute
```

Default dry-run prints counts by tab and does not write.

**Step 4: Run tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/scripts/test_seed_casamento_garapha_content.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/scripts/seed_casamento_garapha_content.py backend/tests/scripts/test_seed_casamento_garapha_content.py
git commit -m "feat: write casamento garapha content to sheets"
```

### Task 4: Import Sheet Content to Supabase

**Files:**
- Modify: `backend/scripts/seed_casamento_garapha_content.py`
- Test: `backend/tests/scripts/test_seed_casamento_garapha_content.py`

**Step 1: Add import orchestration**

When `--execute --import-db` is passed, run these imports after successful sheet writes:

```python
from scripts.import_trip_content import import_one, build_sheets_client
from app.services.admin_service import (
    admin_import_emergency_contacts,
    admin_import_faq,
    admin_import_recommendations,
)
from scripts.import_staff_content import import_one as import_staff_one
```

Use:

- `import_trip_content.import_one(...)` for `Fases`, `Checklist`, `Links`, `Roteiro`, `Recomendacoes`.
- `admin_import_emergency_contacts(TRIP_UUID)` for `Emergency Contacts`.
- `admin_import_faq(TRIP_UUID)` for `FAQ`.
- `import_staff_content.import_one(...)` or the existing parser/writer for `Contatos`.

After imports, call `admin_set_mode(TRIP_UUID, "pre-trip")`.

**Step 2: Keep destructive scope narrow**

All imports should delete/replace only rows or DB records for `CASAMENTO-GARAPHA-2026`, matching existing helper behavior.

**Step 3: Run tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/scripts/test_seed_casamento_garapha_content.py tests/scripts/test_import_trip_content.py tests/scripts/test_import_staff_content.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add backend/scripts/seed_casamento_garapha_content.py backend/tests/scripts/test_seed_casamento_garapha_content.py
git commit -m "feat: import casamento garapha sheet content"
```

### Task 5: Execute Against Sheets and Database

**Files:**
- Generated/updated only by external services: Trip Content Google Sheet, Staff Content Google Sheet, Supabase.

**Step 1: Dry-run**

Run:

```bash
cd backend && .venv/bin/python scripts/seed_casamento_garapha_content.py
```

Expected output includes:

- content tabs updated in dry-run summary;
- staff tabs updated in dry-run summary;
- four pre-trip phases;
- three in-trip days;
- four activities;
- FAQ count;
- recommendation count.

**Step 2: Write to Google Sheets**

Run:

```bash
cd backend && .venv/bin/python scripts/seed_casamento_garapha_content.py --execute
```

Expected: Google Sheets update succeeds and reports updated tabs.

**Step 3: Import to Supabase**

Run:

```bash
cd backend && .venv/bin/python scripts/seed_casamento_garapha_content.py --execute --import-db
```

Expected: imports complete and trip mode remains `pre-trip`.

### Task 6: Verify App-Facing Data

**Files:**
- No code changes.

**Step 1: Verify database counts**

Run a read-only query for `CASAMENTO-GARAPHA-2026` confirming:

- `trip_settings.mode = pre-trip`
- `trip_phases`: 4 pre-trip, 3 in-trip
- `trip_activities`: 4
- `trip_faqs`: 3
- `trip_recommendations`: expected non-placeholder count
- `trip_emergency_contacts`: at least 1
- `trip_contacts`: at least 1

**Step 2: Verify app APIs**

Authenticate as Gabriela or Raphael and call:

- `GET /me/trip`
- `GET /me/trip/phases`
- `GET /me/faq`
- `GET /me/recommendations`
- `GET /me/emergency-contacts`

Expected:

- `/me/trip` reports `trip_mode: pre-trip`.
- `/me/trip/phases` includes both pre-trip and in-trip records in the response.
- Home will display pre-trip phases because the mode remains `pre-trip`.
- Information and recommendations endpoints return the imported wedding content.

**Step 3: Final commit if verification-only adjustments were needed**

If any small fixes were made during execution:

```bash
git add backend/scripts/seed_casamento_garapha_content.py backend/tests/scripts/test_seed_casamento_garapha_content.py
git commit -m "fix: verify casamento garapha content import"
```

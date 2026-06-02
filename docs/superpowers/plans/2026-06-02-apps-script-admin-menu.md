# Apps Script Admin Menu — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar 3 endpoints admin no backend FastAPI e um Apps Script `Code.gs` que adiciona um menu "🦜 Parrot Trips" na planilha Google Sheets com botões para Import, Reset Content e Reset Progress.

**Architecture:** O backend ganha um novo router `/admin` com 3 endpoints POST que reutilizam a lógica existente dos scripts Python. O middleware JWT é bypassado para rotas `/admin` (sem autenticação — acesso controlado por quem tem a planilha). O Apps Script lê a lista de viagens da aba `Viagens` da planilha, exibe um dialog para o usuário escolher, e faz uma chamada HTTP ao backend. O usuário copia e cola o `Code.gs` manualmente no editor Apps Script da planilha.

**Tech Stack:** Python 3.13, FastAPI, asyncpg, Google Apps Script (JavaScript)

---

## Contexto

- Backend URL produção: `https://parrot-trips-backend-428743191336.southamerica-east1.run.app`
- Planilha: `TRIP_CONTENT_SHEET_ID` na aba `Viagens` — colunas: `trip_uuid`, `nome_da_viagem`, `data_inicio`, `data_fim`
- Scripts Python existentes que contêm a lógica a reutilizar:
  - `backend/scripts/import_trip_content.py` → funções `import_one`, `fetch_all_trip_uuids`
  - `backend/scripts/reset_trip_content.py` → lógica de delete em cascata
  - `backend/scripts/reset_traveler_progress.py` → delete de `traveler_checklist_progress` e `traveler_phase_progress`
- JWT middleware bloqueia tudo exceto `/auth` e `/healthz` — admin routes precisam ser adicionadas à lista de exceções

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `backend/app/routers/admin.py` | Criar | 3 endpoints POST admin |
| `backend/app/services/admin_service.py` | Criar | Lógica de import, reset content e reset progress |
| `backend/app/middleware/auth.py` | Modificar | Adicionar `/admin` à lista de paths públicos |
| `backend/app/main.py` | Modificar | Registrar o admin router |
| `google-apps-script/Code.gs` | Criar | Menu Sheets + chamadas HTTP ao backend |

---

## Task 1: Admin service — lógica dos 3 endpoints

**Files:**
- Create: `backend/app/services/admin_service.py`

- [ ] **Step 1: Criar `backend/app/services/admin_service.py`**

```python
"""Admin service: import trip content, reset content, reset traveler progress."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/parrot_trips",
)
PG_URL = (
    DATABASE_URL
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("postgresql+psycopg2://", "postgresql://")
)

TRIP_CONTENT_SHEET_ID = os.environ.get("TRIP_CONTENT_SHEET_ID", "")


async def _get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(PG_URL)


async def admin_import_trip(trip_uuid: str) -> dict:
    """Import trip content from Google Sheets into Supabase."""
    # Import inline to avoid circular deps and heavy imports at startup
    from scripts.import_trip_content import (
        build_sheets_client,
        filter_rows_by_trip,
        parse_checklist_tab,
        parse_fases_tab,
        parse_links_tab,
        parse_roteiro_tab,
        read_tab,
        write_to_db,
    )

    if not TRIP_CONTENT_SHEET_ID:
        raise ValueError("TRIP_CONTENT_SHEET_ID is not set")

    sheets_svc = build_sheets_client()

    fases_rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Fases"), trip_uuid)
    pre_trip_phases = parse_fases_tab(fases_rows)

    checklist_rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Checklist"), trip_uuid)
    parse_checklist_tab(checklist_rows, pre_trip_phases)

    links_rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Links"), trip_uuid)
    parse_links_tab(links_rows, pre_trip_phases)

    roteiro_rows = filter_rows_by_trip(read_tab(sheets_svc, TRIP_CONTENT_SHEET_ID, "Roteiro"), trip_uuid)
    in_trip_days = parse_roteiro_tab(roteiro_rows)

    if not pre_trip_phases and not in_trip_days:
        return {"status": "skipped", "message": f"No data found for trip '{trip_uuid}' in the sheet"}

    conn = await _get_connection()
    try:
        await write_to_db(conn, trip_uuid, pre_trip_phases, in_trip_days)
    finally:
        await conn.close()

    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "phases": len(pre_trip_phases),
        "checklist_items": sum(len(p.checklist) for p in pre_trip_phases),
        "links": sum(len(p.links) for p in pre_trip_phases),
        "days": len(in_trip_days),
        "activities": sum(len(d.activities) for d in in_trip_days),
    }


async def admin_reset_content(trip_uuid: str) -> dict:
    """Delete all trip_phases and child rows for the given trip."""
    conn = await _get_connection()
    try:
        phase_rows = await conn.fetch(
            "SELECT id FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if not phase_rows:
            return {"status": "ok", "message": "No content to delete", "deleted_phases": 0}

        phase_ids = [str(r["id"]) for r in phase_rows]
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        async with conn.transaction():
            if tt_rows:
                tt_ids = [str(r["id"]) for r in tt_rows]
                await conn.execute(
                    "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
                await conn.execute(
                    "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
            await conn.execute(
                "DELETE FROM trip_activities WHERE trip_phase_id = ANY($1::uuid[])", phase_ids
            )
            await conn.execute(
                "DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = ANY($1::uuid[])", phase_ids
            )
            await conn.execute(
                "DELETE FROM trip_phase_links WHERE trip_phase_id = ANY($1::uuid[])", phase_ids
            )
            await conn.execute(
                "DELETE FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
            )
    finally:
        await conn.close()

    return {"status": "ok", "trip_uuid": trip_uuid, "deleted_phases": len(phase_ids)}


async def admin_reset_progress(trip_uuid: str) -> dict:
    """Delete all traveler progress (checklist + phase) for the given trip."""
    conn = await _get_connection()
    try:
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if not tt_rows:
            return {"status": "ok", "message": "No travelers found", "deleted_rows": 0}

        tt_ids = [str(r["id"]) for r in tt_rows]
        async with conn.transaction():
            deleted_checklist = await conn.fetchval(
                "WITH d AS (DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[]) RETURNING 1) SELECT COUNT(*) FROM d",
                tt_ids,
            )
            deleted_phase = await conn.fetchval(
                "WITH d AS (DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[]) RETURNING 1) SELECT COUNT(*) FROM d",
                tt_ids,
            )
    finally:
        await conn.close()

    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "deleted_checklist_progress": deleted_checklist,
        "deleted_phase_progress": deleted_phase,
    }
```

- [ ] **Step 2: Verificar que o arquivo não tem erros de sintaxe**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run python -c "import app.services.admin_service"
```

Expected: sem output (sem erros).

- [ ] **Step 3: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add backend/app/services/admin_service.py
git commit -m "feat: add admin_service with import, reset_content, reset_progress"
```

---

## Task 2: Admin router — 3 endpoints POST

**Files:**
- Create: `backend/app/routers/admin.py`
- Modify: `backend/app/middleware/auth.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Criar `backend/app/routers/admin.py`**

```python
"""Admin HTTP routes — no JWT required, protected by network/sheet access only."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.admin_service import (
    admin_import_trip,
    admin_reset_content,
    admin_reset_progress,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class TripUUIDRequest(BaseModel):
    trip_uuid: str


@router.post("/trips/import")
async def import_trip(body: TripUUIDRequest):
    """Import trip content from Google Sheets into Supabase."""
    try:
        result = await admin_import_trip(body.trip_uuid)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/reset-content")
async def reset_content(body: TripUUIDRequest):
    """Delete all phases, checklist, links and activities for a trip."""
    try:
        result = await admin_reset_content(body.trip_uuid)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/trips/reset-progress")
async def reset_progress(body: TripUUIDRequest):
    """Delete all traveler checklist and phase progress for a trip."""
    try:
        result = await admin_reset_progress(body.trip_uuid)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
```

- [ ] **Step 2: Atualizar `backend/app/middleware/auth.py` para bypassar `/admin`**

Encontrar a linha:
```python
_PUBLIC_PREFIXES = ("/auth",)
```

Substituir por:
```python
_PUBLIC_PREFIXES = ("/auth", "/admin")
```

- [ ] **Step 3: Registrar o router em `backend/app/main.py`**

Adicionar o import:
```python
from app.routers.admin import router as admin_router
```

Adicionar após os outros `include_router`:
```python
app.include_router(admin_router)
```

- [ ] **Step 4: Verificar que o app sobe sem erros**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run python -c "from app.main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add backend/app/routers/admin.py backend/app/middleware/auth.py backend/app/main.py
git commit -m "feat: add /admin router with import, reset-content, reset-progress endpoints"
```

---

## Task 3: Google Apps Script — Code.gs

**Files:**
- Create: `google-apps-script/Code.gs`

Este arquivo não roda no repositório — é para o usuário copiar e colar no editor Apps Script da planilha (`Extensions → Apps Script`).

- [ ] **Step 1: Criar pasta e arquivo**

```bash
mkdir -p /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/google-apps-script
```

Criar `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/google-apps-script/Code.gs`:

```javascript
// Parrot Trips — Admin Menu for Google Sheets
// Paste this entire file into Extensions → Apps Script in the spreadsheet.

var BACKEND_URL = "https://parrot-trips-backend-428743191336.southamerica-east1.run.app";

// Creates the menu automatically when the spreadsheet opens.
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("🦜 Parrot Trips")
    .addItem("Import Trip Content → Supabase", "importTrip")
    .addSeparator()
    .addItem("Reset Trip Content (apaga fases e atividades)", "resetContent")
    .addItem("Reset Traveler Progress (zera barra de progresso)", "resetProgress")
    .addToUi();
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function getTripList() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Viagens");
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Aba 'Viagens' não encontrada na planilha.");
    return null;
  }
  var data = sheet.getDataRange().getValues();
  // Skip header row; columns: trip_uuid, nome_da_viagem, data_inicio, data_fim
  var trips = [];
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    if (row[0]) {
      trips.push({ uuid: String(row[0]), name: String(row[1] || row[0]), date: String(row[2] || "") });
    }
  }
  return trips;
}

function chooseTripDialog(title, confirmLabel) {
  var trips = getTripList();
  if (!trips || trips.length === 0) {
    SpreadsheetApp.getUi().alert("Nenhuma viagem encontrada na aba 'Viagens'.");
    return null;
  }

  // Build a simple HTML dialog with a select dropdown
  var options = trips.map(function(t) {
    return '<option value="' + t.uuid + '">' + t.name + ' (' + t.date + ')</option>';
  }).join("");

  var html = HtmlService.createHtmlOutput(
    '<style>body{font-family:sans-serif;padding:16px;}select,button{width:100%;margin-top:8px;padding:8px;font-size:14px;}</style>' +
    '<p>' + title + '</p>' +
    '<select id="trip">' + options + '</select>' +
    '<button onclick="google.script.run.withSuccessHandler(function(){google.script.host.close()}).withFailureHandler(function(e){alert(e.message);google.script.host.close()})._runAction(document.getElementById(\'trip\').value)">' +
    confirmLabel + '</button>'
  ).setWidth(400).setHeight(160);

  return html;
}

function callBackend(endpoint, trip_uuid) {
  var url = BACKEND_URL + endpoint;
  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ trip_uuid: trip_uuid }),
    muteHttpExceptions: true,
  };
  var response = UrlFetchApp.fetch(url, options);
  var code = response.getResponseCode();
  var body = response.getContentText();
  if (code >= 200 && code < 300) {
    return JSON.parse(body);
  } else {
    throw new Error("Backend error " + code + ": " + body);
  }
}

function showResult(result) {
  var msg = "✅ Concluído!\n\n";
  for (var key in result) {
    if (key !== "status") msg += key + ": " + result[key] + "\n";
  }
  SpreadsheetApp.getUi().alert(msg);
}

// ── Actions — called from dialog buttons ──────────────────────────────────────

// These functions are called via google.script.run from the HTML dialogs.
// They must be global (not nested) so Apps Script can find them.

var _pendingAction = null;

function _runAction(trip_uuid) {
  if (!trip_uuid) return;
  if (_pendingAction === "import") {
    var result = callBackend("/admin/trips/import", trip_uuid);
    showResult(result);
  } else if (_pendingAction === "resetContent") {
    var result = callBackend("/admin/trips/reset-content", trip_uuid);
    showResult(result);
  } else if (_pendingAction === "resetProgress") {
    var result = callBackend("/admin/trips/reset-progress", trip_uuid);
    showResult(result);
  }
}

// ── Menu items ────────────────────────────────────────────────────────────────

function importTrip() {
  _pendingAction = "import";
  var trips = getTripList();
  if (!trips || trips.length === 0) return;
  var ui = SpreadsheetApp.getUi();
  var options = trips.map(function(t) { return t.name + " (" + t.date + ") — " + t.uuid; });
  var result = ui.showInputDialog ?
    null :  // fallback below
    null;

  // Use a simple prompt since Apps Script doesn't have a native dropdown dialog
  var msg = "Digite o trip_uuid da viagem:\n\n" +
    trips.map(function(t, i) { return (i+1) + ". " + t.name + " → " + t.uuid; }).join("\n");
  var response = ui.prompt("🦜 Import Trip Content", msg, ui.ButtonSet.OK_CANCEL);
  if (response.getSelectedButton() !== ui.Button.OK) return;
  var trip_uuid = response.getResponseText().trim();
  if (!trip_uuid) return;

  try {
    var res = callBackend("/admin/trips/import", trip_uuid);
    showResult(res);
  } catch(e) {
    ui.alert("❌ Erro: " + e.message);
  }
}

function resetContent() {
  var ui = SpreadsheetApp.getUi();
  var trips = getTripList();
  if (!trips || trips.length === 0) return;
  var msg = "⚠️ ATENÇÃO: isso apaga todas as fases e atividades do banco para a viagem escolhida.\n\n" +
    "Digite o trip_uuid:\n\n" +
    trips.map(function(t, i) { return (i+1) + ". " + t.name + " → " + t.uuid; }).join("\n");
  var response = ui.prompt("🦜 Reset Trip Content", msg, ui.ButtonSet.OK_CANCEL);
  if (response.getSelectedButton() !== ui.Button.OK) return;
  var trip_uuid = response.getResponseText().trim();
  if (!trip_uuid) return;

  try {
    var res = callBackend("/admin/trips/reset-content", trip_uuid);
    showResult(res);
  } catch(e) {
    ui.alert("❌ Erro: " + e.message);
  }
}

function resetProgress() {
  var ui = SpreadsheetApp.getUi();
  var trips = getTripList();
  if (!trips || trips.length === 0) return;
  var msg = "⚠️ ATENÇÃO: isso zera a barra de progresso de todos os viajantes da viagem escolhida.\n\n" +
    "Digite o trip_uuid:\n\n" +
    trips.map(function(t, i) { return (i+1) + ". " + t.name + " → " + t.uuid; }).join("\n");
  var response = ui.prompt("🦜 Reset Traveler Progress", msg, ui.ButtonSet.OK_CANCEL);
  if (response.getSelectedButton() !== ui.Button.OK) return;
  var trip_uuid = response.getResponseText().trim();
  if (!trip_uuid) return;

  try {
    var res = callBackend("/admin/trips/reset-progress", trip_uuid);
    showResult(res);
  } catch(e) {
    ui.alert("❌ Erro: " + e.message);
  }
}
```

- [ ] **Step 2: Criar `google-apps-script/README.md` com instruções**

Criar `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/google-apps-script/README.md`:

```markdown
# Parrot Trips — Google Apps Script

Menu admin para a planilha Google Sheets. Permite importar conteúdo e resetar dados do Supabase diretamente da planilha.

## Como instalar

1. Abrir a planilha [Parrot Trips — Conteúdo de Viagens](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP)
2. Clicar em **Extensions → Apps Script**
3. Apagar todo o conteúdo do editor
4. Colar o conteúdo de `Code.gs`
5. Salvar (Ctrl+S)
6. Fechar o editor e recarregar a planilha
7. O menu **🦜 Parrot Trips** aparecerá na barra superior

## Funcionalidades

| Menu | O que faz |
|---|---|
| **Import Trip Content → Supabase** | Lê as abas Fases/Checklist/Links/Roteiro da planilha e importa para o banco |
| **Reset Trip Content** | Apaga todas as fases, atividades e checklist do banco para a viagem |
| **Reset Traveler Progress** | Zera a barra de progresso de todos os viajantes (~1 semana antes da partida) |

## Como usar

1. Clicar no menu **🦜 Parrot Trips** → escolher a ação
2. Um dialog abre listando as viagens disponíveis (lidas da aba `Viagens`)
3. Digitar o `trip_uuid` da viagem desejada
4. Confirmar — o resultado aparece em um alert
```

- [ ] **Step 3: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add google-apps-script/
git commit -m "feat: add Google Apps Script admin menu for Sheets"
```

---

## Task 4: Deploy do backend e teste dos endpoints

**Files:** nenhum arquivo novo — apenas execução

- [ ] **Step 1: Build e deploy do backend**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
make deploy-backend
```

Expected ao final:
```
Backend URL:
https://parrot-trips-backend-428743191336.southamerica-east1.run.app
```

- [ ] **Step 2: Testar os 3 endpoints com curl**

```bash
BACKEND=https://parrot-trips-backend-428743191336.southamerica-east1.run.app

# Testar reset-progress (seguro — só apaga progresso)
curl -s -X POST "$BACKEND/admin/trips/reset-progress" \
  -H "Content-Type: application/json" \
  -d '{"trip_uuid": "TEST-2026-FULL"}' | python3 -m json.tool

# Testar import
curl -s -X POST "$BACKEND/admin/trips/import" \
  -H "Content-Type: application/json" \
  -d '{"trip_uuid": "TEST-2026-FULL"}' | python3 -m json.tool
```

Expected para reset-progress:
```json
{
  "status": "ok",
  "trip_uuid": "TEST-2026-FULL",
  "deleted_checklist_progress": 0,
  "deleted_phase_progress": 0
}
```

Expected para import:
```json
{
  "status": "ok",
  "trip_uuid": "TEST-2026-FULL",
  "phases": 4,
  ...
}
```

- [ ] **Step 3: Instalar o Apps Script na planilha**

1. Abrir [a planilha](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP)
2. `Extensions → Apps Script`
3. Apagar conteúdo existente
4. Colar o conteúdo de `google-apps-script/Code.gs`
5. Salvar e fechar
6. Recarregar a planilha — verificar que o menu **🦜 Parrot Trips** aparece

---

## Self-review

**Spec coverage:**
- ✅ 3 endpoints admin: `/admin/trips/import`, `/admin/trips/reset-content`, `/admin/trips/reset-progress`
- ✅ JWT bypassed para `/admin`
- ✅ Apps Script com menu e 3 itens
- ✅ Lista de viagens lida da aba `Viagens` da planilha
- ✅ Dialog com prompt para escolher o trip_uuid
- ✅ README com instruções de instalação
- ✅ Deploy e teste dos endpoints

**Placeholder scan:** Nenhum TBD ou TODO encontrado.

**Consistência de tipos:**
- `TripUUIDRequest.trip_uuid` passado para `admin_import_trip(trip_uuid)` — consistente. ✅
- `callBackend("/admin/trips/import", trip_uuid)` no Apps Script → `POST /admin/trips/import` com body `{trip_uuid}` → `TripUUIDRequest` no FastAPI. ✅

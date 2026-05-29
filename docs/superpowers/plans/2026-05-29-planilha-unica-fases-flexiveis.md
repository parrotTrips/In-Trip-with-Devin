# Planilha Única com Fases Flexíveis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reestruturar a planilha Google Sheets de uma aba `Pre-Trip` key-value para 5 abas flat (`Viagens`, `Fases`, `Checklist`, `Links`, `Roteiro`), tornar as fases pré-trip completamente flexíveis por viagem, e atualizar os scripts e testes correspondentes.

**Architecture:** `create_trip_sheets.py` gera a nova estrutura de 5 abas. `import_trip_content.py` lê as 4 abas de conteúdo, une os dados por `(trip_uuid, fase)` e faz replace completo no banco. A aba `Viagens` é somente referência para quem preenche — não é importada. Fases pré-trip são flexíveis: cada viagem define quais fases tem e em que ordem via coluna `ordem` na aba `Fases`.

**Tech Stack:** Python 3.13, asyncpg, google-api-python-client, pytest

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `backend/scripts/create_trip_sheets.py` | Modificar | Gerar 5 abas em vez de 2 |
| `backend/scripts/import_trip_content.py` | Modificar | Parsers novos, fases flexíveis |
| `backend/tests/scripts/test_import_trip_content.py` | Modificar | Testes para nova estrutura |

---

## Nova estrutura da planilha

### Aba `Viagens` (referência — não importada)
| trip_uuid | nome_da_viagem | data_inicio | data_fim |
|---|---|---|---|
| gsb-nye-2026 | GSB NYE Brazil Trek | 2026-12-26 | 2027-01-04 |

### Aba `Fases`
| trip_uuid | ordem | fase | titulo | subtitulo | icone | descricao_curta | descricao_completa |
|---|---|---|---|---|---|---|---|
| gsb-nye-2026 | 1 | visa | Visto | Requisitos de entrada | passport | Verifique o visto... | Cidadãos americanos... |

### Aba `Checklist`
| trip_uuid | fase | ordem | label | obrigatorio |
|---|---|---|---|---|
| gsb-nye-2026 | visa | 1 | Verificar se sua nacionalidade requer visto | true |

### Aba `Links`
| trip_uuid | fase | ordem | label | url |
|---|---|---|---|---|
| gsb-nye-2026 | visa | 1 | Portal eVisa Brasil | https://... |

### Aba `Roteiro` (sem mudança estrutural)
| trip_uuid | dia | data | dia_titulo | dia_subtitulo | dia_icon | dia_descricao_curta | dia_descricao_completa | atividade_nome | atividade_tipo | atividade_horario | atividade_duracao_min | atividade_descricao_curta | atividade_info_pratica | atividade_preco_brl |

---

## Task 1: Atualizar `create_trip_sheets.py`

**Files:**
- Modify: `backend/scripts/create_trip_sheets.py`

- [ ] **Step 1: Substituir constantes de header e dados de exemplo**

Substituir os blocos `PRE_TRIP_HEADER`, `PRE_TRIP_EXAMPLE_ROWS`, `ROTEIRO_HEADER` e funções `_pre_trip_example_rows`, `_roteiro_example_rows` pelo seguinte:

```python
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
```

- [ ] **Step 2: Substituir `populate_spreadsheet` pela nova versão com 5 abas**

Substituir a função `populate_spreadsheet` inteira por:

```python
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
```

- [ ] **Step 3: Verificar que o script roda sem erros de sintaxe**

```bash
cd backend
poetry run python -c "import scripts.create_trip_sheets"
```
Expected: nenhum output (sem erros).

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/create_trip_sheets.py
git commit -m "feat: reestruturar planilha para 5 abas flat com fases flexíveis"
```

---

## Task 2: Atualizar parsers em `import_trip_content.py`

**Files:**
- Modify: `backend/scripts/import_trip_content.py`

- [ ] **Step 1: Substituir dataclasses e remover TripConfig**

Remover a dataclass `TripConfig` e a função `parse_config_tab`. Manter `ChecklistItem`, `PhaseLink`, `PreTripPhase`, `Activity`, `InTripDay` sem alteração.

Adicionar a constante de colunas do roteiro atualizada (já inclui `trip_uuid` na primeira posição):

```python
_ROTEIRO_COLS = [
    "trip_uuid",
    "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon",
    "dia_descricao_curta", "dia_descricao_completa",
    "atividade_nome", "atividade_tipo", "atividade_horario",
    "atividade_duracao_min", "atividade_descricao_curta",
    "atividade_info_pratica", "atividade_preco_brl",
]
```

- [ ] **Step 2: Substituir `parse_pre_trip_tab` por três parsers flat**

Remover `parse_pre_trip_tab` inteira. Adicionar as três funções abaixo:

```python
def parse_fases_tab(rows: list[list[str]]) -> list[PreTripPhase]:
    """Parse Fases tab (already filtered by trip_uuid). Each row is one complete phase.
    Columns: trip_uuid, ordem, fase, titulo, subtitulo, icone, descricao_curta, descricao_completa
    Returns phases sorted by ordem."""
    phases: list[tuple[int, PreTripPhase]] = []
    for row in rows[1:]:  # skip header
        if len(row) < 8:
            continue
        _, ordem_str, fase, titulo, subtitulo, icone, descricao_curta, descricao_completa = (
            row[i].strip() if i < len(row) else "" for i in range(8)
        )
        if not fase:
            continue
        try:
            ordem = int(ordem_str)
        except ValueError:
            continue
        phases.append((ordem, PreTripPhase(
            fase=fase,
            title=titulo,
            subtitle=subtitulo,
            icon=icone,
            short_description=descricao_curta,
            detailed_description=descricao_completa,
        )))
    return [p for _, p in sorted(phases, key=lambda x: x[0])]


def parse_checklist_tab(rows: list[list[str]], phases: list[PreTripPhase]) -> None:
    """Parse Checklist tab (already filtered by trip_uuid) and attach items to phases in-place.
    Columns: trip_uuid, fase, ordem, label, obrigatorio"""
    phase_map = {p.fase: p for p in phases}
    by_fase: dict[str, dict[int, dict[str, str]]] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 5:
            continue
        _, fase, ordem_str, label, obrigatorio = (
            row[i].strip() if i < len(row) else "" for i in range(5)
        )
        if not fase or not label:
            continue
        try:
            ordem = int(ordem_str)
        except ValueError:
            continue
        if fase not in by_fase:
            by_fase[fase] = {}
        by_fase[fase][ordem] = {"label": label, "obrigatorio": obrigatorio}

    for fase, items in by_fase.items():
        phase = phase_map.get(fase)
        if not phase:
            continue
        for sort_order, fields in sorted(items.items()):
            is_required = fields["obrigatorio"].lower() == "true"
            phase.checklist.append(ChecklistItem(
                label=fields["label"],
                is_required=is_required,
                sort_order=sort_order - 1,
            ))


def parse_links_tab(rows: list[list[str]], phases: list[PreTripPhase]) -> None:
    """Parse Links tab (already filtered by trip_uuid) and attach links to phases in-place.
    Columns: trip_uuid, fase, ordem, label, url"""
    phase_map = {p.fase: p for p in phases}
    by_fase: dict[str, dict[int, dict[str, str]]] = {}

    for row in rows[1:]:  # skip header
        if len(row) < 5:
            continue
        _, fase, ordem_str, label, url = (
            row[i].strip() if i < len(row) else "" for i in range(5)
        )
        if not fase or not label or not url:
            continue
        try:
            ordem = int(ordem_str)
        except ValueError:
            continue
        if fase not in by_fase:
            by_fase[fase] = {}
        by_fase[fase][ordem] = {"label": label, "url": url}

    for fase, links in by_fase.items():
        phase = phase_map.get(fase)
        if not phase:
            continue
        for sort_order, fields in sorted(links.items()):
            phase.links.append(PhaseLink(
                label=fields["label"],
                url=fields["url"],
                sort_order=sort_order - 1,
            ))
```

- [ ] **Step 3: Atualizar `main()` para ler as 4 abas e remover referência a Config**

Substituir o bloco de leitura dentro de `main()`:

```python
async def main(trip_uuid: str, sheet_id: str) -> None:
    if not sheet_id:
        print("ERROR: TRIP_CONTENT_SHEET_ID is not set in backend/.env")
        print("Run create_trip_sheets.py first and add the printed sheet ID to .env")
        sys.exit(1)

    print("Connecting to Google Sheets...")
    sheets_svc = build_sheets_client()

    print("Reading Fases tab...")
    fases_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Fases"), trip_uuid)
    pre_trip_phases = parse_fases_tab(fases_rows)
    print(f"  {len(pre_trip_phases)} fase(s): {[p.fase for p in pre_trip_phases]}")

    print("Reading Checklist tab...")
    checklist_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Checklist"), trip_uuid)
    parse_checklist_tab(checklist_rows, pre_trip_phases)

    print("Reading Links tab...")
    links_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Links"), trip_uuid)
    parse_links_tab(links_rows, pre_trip_phases)

    total_checklist = sum(len(p.checklist) for p in pre_trip_phases)
    total_links = sum(len(p.links) for p in pre_trip_phases)

    print("Reading Roteiro tab...")
    roteiro_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Roteiro"), trip_uuid)
    in_trip_days = parse_roteiro_tab(roteiro_rows)
    total_activities = sum(len(d.activities) for d in in_trip_days)
    print(f"  {len(in_trip_days)} day(s), {total_activities} activit(ies)")

    if not pre_trip_phases and not in_trip_days:
        print(f"\nNo data found for trip_uuid='{trip_uuid}'. Check the sheet and try again.")
        sys.exit(1)

    print("\nConnecting to database...")
    conn = await asyncpg.connect(PG_URL)
    try:
        await write_to_db(conn, trip_uuid, pre_trip_phases, in_trip_days)
    finally:
        await conn.close()

    print("\n✅ Import complete!")
    print(f"   Pre-trip phases : {len(pre_trip_phases)}")
    print(f"   Checklist items : {total_checklist}")
    print(f"   Links           : {total_links}")
    print(f"   In-trip days    : {len(in_trip_days)}")
    print(f"   Activities      : {total_activities}")
```

- [ ] **Step 4: Atualizar `write_to_db` para usar a ordem da planilha em vez de `FIXED_PHASE_ORDER`**

Localizar em `write_to_db` o bloco `# 2. Insert pre-trip phases` e substituir:

```python
        # 2. Insert pre-trip phases — order comes from the spreadsheet (sort_order already set)
        for phase in pre_trip_phases:
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
```

(Remover também as linhas `FIXED_PHASE_ORDER = [...]` e `phase_map = {p.fase: p for p in pre_trip_phases}` que ficavam antes desse bloco.)

- [ ] **Step 5: Verificar que o script roda sem erros de sintaxe**

```bash
cd backend
poetry run python -c "import scripts.import_trip_content"
```
Expected: nenhum output.

- [ ] **Step 6: Commit**

```bash
git add backend/scripts/import_trip_content.py
git commit -m "feat: parsers flat para Fases/Checklist/Links, fases flexíveis"
```

---

## Task 3: Atualizar testes

**Files:**
- Modify: `backend/tests/scripts/test_import_trip_content.py`

- [ ] **Step 1: Substituir o arquivo de testes inteiro**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_trip_content import (
    PreTripPhase,
    ChecklistItem,
    PhaseLink,
    InTripDay,
    Activity,
    filter_rows_by_trip,
    parse_fases_tab,
    parse_checklist_tab,
    parse_links_tab,
    parse_roteiro_tab,
)


# ---------------------------------------------------------------------------
# filter_rows_by_trip
# ---------------------------------------------------------------------------

def test_filter_rows_by_trip_keeps_header_and_matching():
    rows = [
        ["trip_uuid", "ordem", "fase", "titulo", "subtitulo", "icone", "descricao_curta", "descricao_completa"],
        ["gsb-nye-2026", "1", "visa", "Visto", "Req", "passport", "Desc", "Detalhe"],
        ["k-latam-2026", "1", "visa", "Visto", "Req", "passport", "Desc", "Detalhe"],
        ["gsb-nye-2026", "2", "vaccination", "Vacinas", "Saúde", "syringe", "Desc", "Detalhe"],
    ]
    result = filter_rows_by_trip(rows, "gsb-nye-2026")
    assert len(result) == 3  # header + 2 matching rows
    assert result[0] == rows[0]
    assert result[1][0] == "gsb-nye-2026"
    assert result[2][0] == "gsb-nye-2026"


def test_filter_rows_by_trip_empty_sheet():
    assert filter_rows_by_trip([], "any-trip") == []


def test_filter_rows_by_trip_no_match():
    rows = [
        ["trip_uuid", "ordem", "fase"],
        ["other-trip", "1", "visa"],
    ]
    result = filter_rows_by_trip(rows, "gsb-nye-2026")
    assert result == [rows[0]]


# ---------------------------------------------------------------------------
# parse_fases_tab
# ---------------------------------------------------------------------------

def test_parse_fases_tab_basic():
    rows = [
        ["trip_uuid", "ordem", "fase", "titulo", "subtitulo", "icone", "descricao_curta", "descricao_completa"],
        ["gsb-nye-2026", "1", "visa", "Visto", "Req de entrada", "passport", "Verifique.", "Detalhe."],
        ["gsb-nye-2026", "2", "packing", "Mala", "O que levar", "luggage", "Dicas.", "Mais dicas."],
    ]
    phases = parse_fases_tab(rows)
    assert len(phases) == 2
    assert phases[0].fase == "visa"
    assert phases[0].title == "Visto"
    assert phases[0].icon == "passport"
    assert phases[1].fase == "packing"


def test_parse_fases_tab_respects_ordem():
    rows = [
        ["trip_uuid", "ordem", "fase", "titulo", "subtitulo", "icone", "descricao_curta", "descricao_completa"],
        ["gsb-nye-2026", "3", "documents", "Docs", "", "file-text", "", ""],
        ["gsb-nye-2026", "1", "visa", "Visto", "", "passport", "", ""],
        ["gsb-nye-2026", "2", "packing", "Mala", "", "luggage", "", ""],
    ]
    phases = parse_fases_tab(rows)
    assert [p.fase for p in phases] == ["visa", "packing", "documents"]


def test_parse_fases_tab_skips_incomplete_rows():
    rows = [
        ["trip_uuid", "ordem", "fase", "titulo", "subtitulo", "icone", "descricao_curta", "descricao_completa"],
        [],
        ["gsb-nye-2026", "1", "visa", "Visto", "", "passport", "", ""],
    ]
    phases = parse_fases_tab(rows)
    assert len(phases) == 1


# ---------------------------------------------------------------------------
# parse_checklist_tab
# ---------------------------------------------------------------------------

def test_parse_checklist_tab_attaches_to_phases():
    phases = [
        PreTripPhase(fase="visa", title="Visto", subtitle="", icon="", short_description="", detailed_description=""),
    ]
    rows = [
        ["trip_uuid", "fase", "ordem", "label", "obrigatorio"],
        ["gsb-nye-2026", "visa", "1", "Verificar necessidade de visto", "true"],
        ["gsb-nye-2026", "visa", "2", "Solicitar eVisa", "false"],
    ]
    parse_checklist_tab(rows, phases)
    assert len(phases[0].checklist) == 2
    assert phases[0].checklist[0].label == "Verificar necessidade de visto"
    assert phases[0].checklist[0].is_required is True
    assert phases[0].checklist[1].is_required is False


def test_parse_checklist_tab_ignores_unknown_fase():
    phases = [
        PreTripPhase(fase="visa", title="", subtitle="", icon="", short_description="", detailed_description=""),
    ]
    rows = [
        ["trip_uuid", "fase", "ordem", "label", "obrigatorio"],
        ["gsb-nye-2026", "unknown_fase", "1", "Item", "true"],
    ]
    parse_checklist_tab(rows, phases)
    assert phases[0].checklist == []


# ---------------------------------------------------------------------------
# parse_links_tab
# ---------------------------------------------------------------------------

def test_parse_links_tab_attaches_to_phases():
    phases = [
        PreTripPhase(fase="visa", title="", subtitle="", icon="", short_description="", detailed_description=""),
    ]
    rows = [
        ["trip_uuid", "fase", "ordem", "label", "url"],
        ["gsb-nye-2026", "visa", "1", "Portal eVisa", "https://www.gov.br"],
    ]
    parse_links_tab(rows, phases)
    assert len(phases[0].links) == 1
    assert phases[0].links[0].url == "https://www.gov.br"


def test_parse_links_tab_skips_missing_url():
    phases = [
        PreTripPhase(fase="visa", title="", subtitle="", icon="", short_description="", detailed_description=""),
    ]
    rows = [
        ["trip_uuid", "fase", "ordem", "label", "url"],
        ["gsb-nye-2026", "visa", "1", "Label sem URL", ""],
    ]
    parse_links_tab(rows, phases)
    assert phases[0].links == []


# ---------------------------------------------------------------------------
# parse_roteiro_tab
# ---------------------------------------------------------------------------

def test_parse_roteiro_tab_basic():
    rows = [
        [
            "trip_uuid", "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon",
            "dia_descricao_curta", "dia_descricao_completa",
            "atividade_nome", "atividade_tipo", "atividade_horario",
            "atividade_duracao_min", "atividade_descricao_curta",
            "atividade_info_pratica", "atividade_preco_brl",
        ],
        [
            "gsb-nye-2026", "1", "2026-12-26", "Day 1 — Dec 26", "Chegada", "plane-landing",
            "Transfer e check-in", "Bem-vindos ao Rio!",
            "Transfer do Aeroporto", "logistics", "14:00",
            "120", "Recepção no aeroporto", "Procurar placa Parrot Trips", "",
        ],
        [
            "gsb-nye-2026", "1", "2026-12-26", "Day 1 — Dec 26", "Chegada", "plane-landing",
            "Transfer e check-in", "Bem-vindos ao Rio!",
            "Welcome Happy Hour", "included", "18:00",
            "240", "Open bar na praia", "", "",
        ],
        [
            "gsb-nye-2026", "2", "2026-12-27", "Day 2 — Dec 27", "Passeio", "sun",
            "Dia de praia", "Curta o Rio!",
            "Praia de Ipanema", "suggested", "09:00",
            "", "Aproveite a praia", "", "",
        ],
    ]
    days = parse_roteiro_tab(rows)
    assert len(days) == 2
    assert days[0].dia == 1
    assert days[0].data == "2026-12-26"
    assert len(days[0].activities) == 2
    assert days[0].activities[0].name == "Transfer do Aeroporto"
    assert days[0].activities[0].duration_minutes == 120
    assert days[1].dia == 2
    assert days[1].activities[0].duration_minutes is None


def test_parse_roteiro_tab_optional_price():
    rows = [
        [
            "trip_uuid", "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon",
            "dia_descricao_curta", "dia_descricao_completa",
            "atividade_nome", "atividade_tipo", "atividade_horario",
            "atividade_duracao_min", "atividade_descricao_curta",
            "atividade_info_pratica", "atividade_preco_brl",
        ],
        [
            "gsb-nye-2026", "1", "2026-12-26", "Day 1", "", "sun", "desc", "",
            "Bike Tour", "optional", "09:00", "180", "Tour de bicicleta", "", "150",
        ],
    ]
    days = parse_roteiro_tab(rows)
    assert days[0].activities[0].amount_brl == 150.0
```

- [ ] **Step 2: Rodar os testes — devem falhar porque o código ainda não foi atualizado**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py -v
```
Expected: falhas em `parse_fases_tab`, `parse_checklist_tab`, `parse_links_tab` (ainda não existem).

- [ ] **Step 3: Após Task 2 completa, rodar os testes — devem passar todos**

```bash
cd backend
poetry run pytest tests/scripts/test_import_trip_content.py -v
```
Expected: todos PASSED.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/scripts/test_import_trip_content.py
git commit -m "test: atualizar testes para nova estrutura flat de fases"
```

---

## Task 4: Recriar planilha no Drive e importar viagem de teste

**Files:** nenhum arquivo de código — apenas execução de scripts

- [ ] **Step 1: Apagar o token OAuth para forçar nova autenticação com scopes corretos**

```bash
cd backend
rm -f secrets/gcp-oauth2-token.json
```

- [ ] **Step 2: Deletar a planilha antiga do Drive manualmente**

Acessar a [pasta do Drive](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP) e deletar o arquivo `"Parrot Trips — Conteúdo de Viagens"` existente (e quaisquer planilhas antigas restantes).

- [ ] **Step 3: Criar nova planilha com estrutura de 5 abas**

```bash
cd backend
poetry run python scripts/create_trip_sheets.py \
  --folder-id 1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP \
  --use-adc
```
Expected: autenticação OAuth no browser, depois:
```
✅ Creating: Parrot Trips — Conteúdo de Viagens...
Done. Sheet ID: <novo_id>
Add to backend/.env:  TRIP_CONTENT_SHEET_ID=<novo_id>
```

- [ ] **Step 4: Atualizar `TRIP_CONTENT_SHEET_ID` no `.env`**

Editar `backend/.env` e substituir o valor de `TRIP_CONTENT_SHEET_ID` pelo novo ID impresso.

- [ ] **Step 5: Apagar o token novamente (scopes de write vs read)**

```bash
rm -f secrets/gcp-oauth2-token.json
```

- [ ] **Step 6: Importar a viagem de teste**

```bash
cd backend
poetry run python scripts/import_trip_content.py --trip-uuid TEST-2026-FULL
```
Expected:
```
✅ Import complete!
   Pre-trip phases : 4
   Checklist items : 8
   Links           : 4
   In-trip days    : 1
   Activities      : 1
```

- [ ] **Step 7: Commit final**

```bash
git add backend/.env.example backend/scripts/ backend/tests/
git commit -m "chore: recriar planilha única com estrutura de 5 abas flat"
```

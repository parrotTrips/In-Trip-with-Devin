import sys
import asyncio
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts import seed_casamento_garapha_content as script


def rows_as_dicts(tab: str, rows: list[list[object]]) -> list[dict[str, object]]:
    header = script.MANAGED_HEADERS[tab]
    return [dict(zip(header, row, strict=True)) for row in rows]


def test_trip_uuid_is_casamento_garapha():
    assert script.TRIP_UUID == "CASAMENTO-GARAPHA-2026"


def test_build_sheet_rows_returns_four_pre_trip_phases():
    rows = script.build_sheet_rows()["content"]["Fases"]
    phases = rows_as_dicts("Fases", rows)

    assert [phase["fase"] for phase in phases] == [
        "logistica_de_viagem",
        "preparando_as_malas",
        "cuidados_e_bem_estar",
        "informacoes_do_casamento",
    ]
    assert {phase["trip_uuid"] for phase in phases} == {script.TRIP_UUID}


def test_checklist_includes_all_pre_trip_content_groups():
    rows = script.build_sheet_rows()["content"]["Checklist"]
    items = rows_as_dicts("Checklist", rows)

    labels_by_phase = {
        phase: {item["label"] for item in items if item["fase"] == phase}
        for phase in {
            "logistica_de_viagem",
            "preparando_as_malas",
            "cuidados_e_bem_estar",
            "informacoes_do_casamento",
        }
    }

    assert "Confirmar voos de chegada e retorno" in labels_by_phase["logistica_de_viagem"]
    assert "Separar roupa para o casamento" in labels_by_phase["preparando_as_malas"]
    assert "Levar protetor solar, repelente e medicacao pessoal" in labels_by_phase["cuidados_e_bem_estar"]
    assert "Revisar site do casamento e lista de presentes" in labels_by_phase["informacoes_do_casamento"]


def test_roteiro_returns_four_activities_across_three_days():
    rows = script.build_sheet_rows()["content"]["Roteiro"]
    activities = rows_as_dicts("Roteiro", rows)

    assert [activity["atividade_nome"] for activity in activities] == [
        "Jantar de Boas Vindas",
        "Passeio de Jangada",
        "Festa Pre Wedding",
        "Casamento",
    ]
    assert {(activity["dia"], activity["data"]) for activity in activities} == {
        (1, "2026-09-04"),
        (2, "2026-09-05"),
        (3, "2026-09-06"),
    }


def test_roteiro_rows_for_same_day_share_day_metadata():
    rows = script.build_sheet_rows()["content"]["Roteiro"]
    activities = rows_as_dicts("Roteiro", rows)
    day_metadata_fields = [
        "data",
        "dia_titulo",
        "dia_subtitulo",
        "dia_icon",
        "dia_descricao_curta",
        "dia_descricao_completa",
    ]

    expected_by_day = {}
    for activity in activities:
        metadata = tuple(activity[field] for field in day_metadata_fields)
        expected_by_day.setdefault(activity["dia"], metadata)

        assert metadata == expected_by_day[activity["dia"]]


def test_faq_returns_three_filled_rows():
    rows = script.build_sheet_rows()["content"]["FAQ"]
    faqs = rows_as_dicts("FAQ", rows)

    assert len(faqs) == 3
    assert [faq["sort_order"] for faq in faqs] == [1, 2, 3]
    assert {faq["question"] for faq in faqs} == {
        "Qual e o traje do casamento?",
        "Havera transporte para os eventos?",
        "Que horas devo chegar para a cerimonia?",
    }
    assert all(faq["answer"] for faq in faqs)


def test_recommendations_skip_placeholders_and_include_real_rows():
    rows = script.build_sheet_rows()["content"]["Recomendacoes"]
    recommendations = rows_as_dicts("Recomendacoes", rows)
    names = {recommendation["name"] for recommendation in recommendations}

    assert recommendations
    assert all(recommendation["name"] for recommendation in recommendations)
    assert all("placeholder" not in str(recommendation["name"]).lower() for recommendation in recommendations)
    assert names >= {
        "Aulas de Yoga, Canoa Havaiana e Kayak / Espaco Imparti",
        "Aulas de Kitesurf - Professor Bete",
        "Lucas - Guia e Aluguel Quadri",
        "Ianaele - Cabelo e Maquiagem",
        "Jimmy - Transfer Aeroporto Jeri - Prea e Taxi",
        "Balcon",
        "Rancho do Peixe",
        "Alisios",
        "Restaurante da Lu",
        "Casinha",
        "Restaurante Caboclo",
        "Restaurante Arriegua",
    }
    assert {recommendation["category"] for recommendation in recommendations} >= {
        "Esportes",
        "Turismo",
        "Beleza",
        "Transporte",
        "Restaurantes",
    }


def test_emergency_contacts_contains_marine_carneiro():
    rows = script.build_sheet_rows()["content"]["Emergency Contacts"]
    contacts = rows_as_dicts("Emergency Contacts", rows)

    assert any(contact["name"] == "Marine Carneiro" for contact in contacts)


def test_staff_contacts_contains_marine_carneiro():
    rows = script.build_sheet_rows()["staff"]["Contatos"]
    contacts = rows_as_dicts("Contatos", rows)

    assert any(contact["name"] == "Marine Carneiro" for contact in contacts)


def test_build_sheet_rows_match_managed_header_widths():
    sheet_rows = script.build_sheet_rows()

    for sheet in sheet_rows.values():
        for tab, rows in sheet.items():
            header = script.MANAGED_HEADERS[tab]

            assert all(len(row) == len(header) for row in rows), tab


def test_build_sheet_rows_returns_copied_rows():
    first_rows = script.build_sheet_rows()
    first_rows["content"]["Viagens"][0][1] = "Mutated title"

    later_rows = script.build_sheet_rows()

    assert later_rows["content"]["Viagens"][0][1] == script.TRIP_TITLE


class FakeRequest:
    def __init__(self, result=None, callback=None):
        self.result = result or {}
        self.callback = callback

    def execute(self):
        if self.callback:
            self.callback()
        return self.result


class FakeSheetsValues:
    def __init__(self, parent):
        self.parent = parent

    def get(self, spreadsheetId, range):
        self.parent.calls.append(("get", spreadsheetId, range))
        tab = range.split("'!")[0].strip("'")
        return FakeRequest({"values": self.parent.values.get((spreadsheetId, tab), [])})

    def clear(self, spreadsheetId, range):
        self.parent.calls.append(("clear", spreadsheetId, range))
        return FakeRequest()

    def update(self, spreadsheetId, range, valueInputOption, body):
        self.parent.calls.append(("update", spreadsheetId, range, valueInputOption, body))
        tab = range.split("'!")[0].strip("'")

        def store():
            self.parent.values[(spreadsheetId, tab)] = body["values"]

        return FakeRequest(callback=store)


class FakeSheetsSpreadsheets:
    def __init__(self, parent):
        self.parent = parent
        self.values_resource = FakeSheetsValues(parent)

    def get(self, spreadsheetId, fields):
        self.parent.calls.append(("meta", spreadsheetId, fields))
        titles = self.parent.tabs.get(spreadsheetId, set())
        return FakeRequest({"sheets": [{"properties": {"title": title}} for title in sorted(titles)]})

    def batchUpdate(self, spreadsheetId, body):
        self.parent.calls.append(("batchUpdate", spreadsheetId, body))
        title = body["requests"][0]["addSheet"]["properties"]["title"]

        def add_tab():
            self.parent.tabs.setdefault(spreadsheetId, set()).add(title)

        return FakeRequest(callback=add_tab)

    def values(self):
        return self.values_resource


class FakeSheets:
    def __init__(self):
        self.calls = []
        self.tabs = {}
        self.values = {}
        self.spreadsheets_resource = FakeSheetsSpreadsheets(self)

    def spreadsheets(self):
        return self.spreadsheets_resource


def trim_trailing_empty(row):
    trimmed = list(row)
    while trimmed and trimmed[-1] == "":
        trimmed.pop()
    return trimmed


def test_merge_trip_rows_preserves_existing_rows_for_other_trips():
    header = script.MANAGED_HEADERS["FAQ"]
    other_trip_row = ["OTHER-2026", "Other question", "Other answer", 1]
    stale_row = [script.TRIP_UUID, "Old question", "Old answer", 2]
    fresh_row = [script.TRIP_UUID, "Fresh question", "Fresh answer", 3]

    merged = script.merge_trip_rows([header, other_trip_row, stale_row], header, [fresh_row])

    assert merged == [header, other_trip_row, fresh_row]


def test_replace_trip_rows_removes_existing_trip_rows_before_appending_fresh_rows():
    sheets = FakeSheets()
    spreadsheet_id = "content-sheet"
    tab = "FAQ"
    header = script.MANAGED_HEADERS[tab]
    other_trip_row = ["OTHER-2026", "Other question", "Other answer", 1]
    stale_row = [script.TRIP_UUID, "Old question", "Old answer", 2]
    second_stale_row = [script.TRIP_UUID, "Older question", "Older answer", 4]
    fresh_row = [script.TRIP_UUID, "Fresh question", "Fresh answer", 3]
    sheets.tabs[spreadsheet_id] = {tab}
    sheets.values[(spreadsheet_id, tab)] = [header, other_trip_row, stale_row, second_stale_row]

    script.replace_trip_rows(sheets, spreadsheet_id, tab, [fresh_row])

    updated_rows = sheets.values[(spreadsheet_id, tab)]
    assert [trim_trailing_empty(row) for row in updated_rows] == [header, other_trip_row, fresh_row, []]
    assert all(len(row) == 26 for row in updated_rows)
    assert not any(call[0] == "clear" for call in sheets.calls)
    assert any(call[:3] == ("update", spreadsheet_id, f"'{tab}'!A:Z") for call in sheets.calls)


def test_replace_trip_rows_rejects_managed_header_mismatch_without_writing():
    sheets = FakeSheets()
    spreadsheet_id = "content-sheet"
    tab = "FAQ"
    wrong_header = ["trip_uuid", "question", "sort_order", "answer"]
    sheets.tabs[spreadsheet_id] = {tab}
    sheets.values[(spreadsheet_id, tab)] = [wrong_header, [script.TRIP_UUID, "Old question", 1, "Old answer"]]

    with pytest.raises(ValueError, match="Header mismatch for managed tab FAQ"):
        script.replace_trip_rows(sheets, spreadsheet_id, tab, [[script.TRIP_UUID, "Fresh question", "Fresh answer", 1]])

    assert not any(call[0] == "update" for call in sheets.calls)
    assert not any(call[0] == "clear" for call in sheets.calls)


def test_replace_trip_rows_uses_managed_header_for_missing_tabs():
    sheets = FakeSheets()
    spreadsheet_id = "content-sheet"
    tab = "FAQ"
    fresh_row = [script.TRIP_UUID, "Fresh question", "Fresh answer", 1]
    sheets.tabs[spreadsheet_id] = set()

    script.replace_trip_rows(sheets, spreadsheet_id, tab, [fresh_row])

    assert [trim_trailing_empty(row) for row in sheets.values[(spreadsheet_id, tab)]] == [
        script.MANAGED_HEADERS[tab],
        fresh_row,
    ]
    assert all(len(row) == 26 for row in sheets.values[(spreadsheet_id, tab)])
    assert ("batchUpdate", spreadsheet_id, {"requests": [{"addSheet": {"properties": {"title": tab}}}]}) in sheets.calls
    assert ("get", spreadsheet_id, f"'{tab}'!A:Z") in sheets.calls


def test_update_sheets_writes_content_and_staff_tabs(monkeypatch):
    calls = []

    def fake_replace_trip_rows(sheets, spreadsheet_id, tab, new_rows):
        calls.append((sheets, spreadsheet_id, tab, new_rows))

    monkeypatch.setattr(script, "replace_trip_rows", fake_replace_trip_rows)
    sheets = object()
    rows = {
        "content": {"FAQ": [["content row"]]},
        "staff": {"Contatos": [["staff row"]]},
    }

    result = script.update_sheets(sheets, rows)

    assert calls == [
        (sheets, script.TRIP_CONTENT_SHEET_ID, "FAQ", [["content row"]]),
        (sheets, script.STAFF_CONTENT_SHEET_ID, "Contatos", [["staff row"]]),
    ]
    assert result["updated_tabs"] == {"content": ["FAQ"], "staff": ["Contatos"]}


def test_cli_dry_run_prints_counts_without_writing(monkeypatch, capsys):
    def fail_build_sheets_client():
        raise AssertionError("dry-run must not build a Sheets client")

    def fail_update_sheets(sheets, rows):
        raise AssertionError("dry-run must not write sheets")

    monkeypatch.setattr(script, "build_sheets_client", fail_build_sheets_client)
    monkeypatch.setattr(script, "update_sheets", fail_update_sheets)

    script.main([])

    output = capsys.readouterr().out
    assert "Dry run: no sheets were written" in output
    assert "content.Fases: 4 rows" in output
    assert "staff.Contatos: 1 rows" in output


def test_cli_execute_writes_sheets(monkeypatch):
    fake_sheets = object()
    written = {}

    monkeypatch.setattr(script, "build_sheets_client", lambda: fake_sheets)

    def fake_update_sheets(sheets, rows):
        written["sheets"] = sheets
        written["rows"] = rows
        return {"updated_tabs": {"content": ["FAQ"], "staff": ["Contatos"]}}

    monkeypatch.setattr(script, "update_sheets", fake_update_sheets)

    script.main(["--execute"])

    assert written["sheets"] is fake_sheets
    assert written["rows"] == script.build_sheet_rows()


def test_cli_rejects_import_db_without_execute(capsys):
    with pytest.raises(SystemExit) as exc_info:
        script.main(["--import-db"])

    assert exc_info.value.code == 2
    assert "--import-db requires --execute" in capsys.readouterr().err


def test_cli_execute_import_db_runs_import_after_successful_sheet_write(monkeypatch):
    fake_sheets = object()
    events = []

    monkeypatch.setattr(script, "build_sheets_client", lambda: fake_sheets)

    def fake_update_sheets(sheets, rows):
        events.append(("write", sheets, rows))
        return {"updated_tabs": {"content": ["FAQ"], "staff": ["Contatos"]}}

    async def fake_import_db_content(sheets):
        events.append(("import", sheets))
        return {"mode": {"mode": "pre-trip"}}

    monkeypatch.setattr(script, "update_sheets", fake_update_sheets)
    monkeypatch.setattr(script, "import_db_content", fake_import_db_content)

    script.main(["--execute", "--import-db"])

    assert events == [
        ("write", fake_sheets, script.build_sheet_rows()),
        ("import", fake_sheets),
    ]


def test_import_db_content_orchestrates_scoped_existing_imports(monkeypatch):
    from app.services import admin_service
    from scripts import import_staff_content, import_trip_content

    class FakeConnection:
        async def close(self):
            events.append(("close",))

    fake_sheets = object()
    fake_conn = FakeConnection()
    events = []

    def fake_build_sheets_client():
        events.append(("build_sheets_client",))
        return fake_sheets

    async def fake_connect(pg_url):
        events.append(("connect", pg_url))
        return fake_conn

    async def fake_trip_import_one(sheets, conn, trip_uuid, sheet_id):
        events.append(("trip_import_one", sheets, conn, trip_uuid, sheet_id))
        return {"phases": 4}

    async def fake_staff_import_one(sheets, conn, trip_uuid, sheet_id):
        events.append(("staff_import_one", sheets, conn, trip_uuid, sheet_id))
        return {"contacts": 1}

    async def fake_admin_import_recommendations(trip_uuid):
        events.append(("admin_import_recommendations", trip_uuid))
        return {"recommendations_imported": 12}

    async def fake_admin_import_emergency_contacts(trip_uuid):
        events.append(("admin_import_emergency_contacts", trip_uuid))
        return {"emergency_contacts_imported": 1}

    async def fake_admin_import_faq(trip_uuid):
        events.append(("admin_import_faq", trip_uuid))
        return {"imported": 3}

    async def fake_admin_set_mode(trip_uuid, mode):
        events.append(("admin_set_mode", trip_uuid, mode))
        return {"mode": mode}

    monkeypatch.setattr(import_trip_content, "build_sheets_client", fake_build_sheets_client)
    monkeypatch.setattr(import_trip_content.asyncpg, "connect", fake_connect)
    monkeypatch.setattr(import_trip_content, "import_one", fake_trip_import_one)
    monkeypatch.setattr(import_staff_content, "import_one", fake_staff_import_one)
    monkeypatch.setattr(admin_service, "admin_import_recommendations", fake_admin_import_recommendations)
    monkeypatch.setattr(admin_service, "admin_import_emergency_contacts", fake_admin_import_emergency_contacts)
    monkeypatch.setattr(admin_service, "admin_import_faq", fake_admin_import_faq)
    monkeypatch.setattr(admin_service, "admin_set_mode", fake_admin_set_mode)

    result = asyncio.run(script.import_db_content())

    assert events == [
        ("build_sheets_client",),
        ("connect", import_trip_content.PG_URL),
        ("trip_import_one", fake_sheets, fake_conn, script.TRIP_UUID, script.TRIP_CONTENT_SHEET_ID),
        ("admin_import_recommendations", script.TRIP_UUID),
        ("admin_import_emergency_contacts", script.TRIP_UUID),
        ("admin_import_faq", script.TRIP_UUID),
        ("staff_import_one", fake_sheets, fake_conn, script.TRIP_UUID, script.STAFF_CONTENT_SHEET_ID),
        ("admin_set_mode", script.TRIP_UUID, "pre-trip"),
        ("close",),
    ]
    assert result == {
        "trip_content": {"phases": 4},
        "recommendations": {"recommendations_imported": 12},
        "emergency_contacts": {"emergency_contacts_imported": 1},
        "faq": {"imported": 3},
        "staff_content": {"contacts": 1},
        "mode": {"mode": "pre-trip"},
    }

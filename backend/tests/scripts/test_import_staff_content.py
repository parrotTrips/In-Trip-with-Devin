import sys
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_staff_content import (
    StaffTaskImportError,
    _require_single_row,
    parse_staff_tasks_tab,
    write_staff_tasks,
)


def test_parse_staff_tasks_tab_basic():
    rows = [
        ["trip_uuid", "dia", "atividade_nome", "staff_phone", "titulo", "descricao", "sort_order"],
        [
            "TEST-2026-FULL",
            "1",
            "Airport Transfer",
            "+5511999990001",
            "Coordenar van 1",
            "Receber viajantes no aeroporto",
            "1",
        ],
    ]

    tasks = parse_staff_tasks_tab(rows)

    assert tasks == [
        {
            "trip_uuid": "TEST-2026-FULL",
            "dia": 1,
            "atividade_nome": "Airport Transfer",
            "staff_phone": "+5511999990001",
            "titulo": "Coordenar van 1",
            "descricao": "Receber viajantes no aeroporto",
            "sort_order": 1,
        }
    ]


def test_parse_staff_tasks_tab_skips_rows_without_title():
    rows = [
        ["trip_uuid", "dia", "atividade_nome", "staff_phone", "titulo", "descricao", "sort_order"],
        ["TEST-2026-FULL", "1", "Airport Transfer", "+5511999990001", "", "Sem titulo", "1"],
    ]

    assert parse_staff_tasks_tab(rows) == []


def test_require_single_row_returns_row():
    row = {"id": "abc"}

    assert _require_single_row([row], "activity", "Airport Transfer") == row


def test_require_single_row_fails_when_missing():
    with pytest.raises(StaffTaskImportError, match="activity not found"):
        _require_single_row([], "activity", "Airport Transfer")


def test_require_single_row_fails_when_duplicate():
    with pytest.raises(StaffTaskImportError, match="activity is ambiguous"):
        _require_single_row([{"id": "a"}, {"id": "b"}], "activity", "Airport Transfer")


class _FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeConn:
    def __init__(self):
        self.fetch_calls = []
        self.phase_id = uuid4()
        self.activity_id = uuid4()
        self.staff_id = uuid4()

    def transaction(self):
        return _FakeTransaction()

    async def fetch(self, query, *args):
        self.fetch_calls.append((query, args))
        if "FROM trip_phases WHERE wetravel_trip_uuid" in query:
            return [{"id": self.phase_id}]
        if "FROM users" in query:
            return [{"id": self.staff_id}]
        if "day_number = $2" in query:
            return [{"id": self.phase_id}]
        if "FROM trip_activities" in query:
            return [{"id": self.activity_id}]
        return []

    async def execute(self, *args):
        return None


@pytest.mark.asyncio
async def test_write_staff_tasks_resolves_dia_as_in_trip_day_number():
    conn = _FakeConn()

    await write_staff_tasks(conn, "TEST-2026-FULL", [{
        "dia": 1,
        "atividade_nome": "Airport Transfer",
        "staff_phone": "+5512991296651",
        "titulo": "Coordenar van 1",
        "descricao": "Receber viajantes no aeroporto",
        "sort_order": 1,
    }])

    day_lookup = [
        query for query, args in conn.fetch_calls
        if "day_number = $2" in query and args == ("TEST-2026-FULL", 1)
    ]
    assert day_lookup

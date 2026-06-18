import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_staff_content import parse_staff_tasks_tab


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

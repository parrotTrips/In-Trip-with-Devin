import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_trip_content import (
    PreTripPhase,
    ChecklistItem,
    PhaseLink,
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
    assert days[0].title == "Day 1 — Dec 26"
    assert days[0].subtitle == "Chegada"
    assert len(days[0].activities) == 2
    assert days[0].activities[0].name == "Transfer do Aeroporto"
    assert days[0].activities[0].activity_type == "logistics"
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

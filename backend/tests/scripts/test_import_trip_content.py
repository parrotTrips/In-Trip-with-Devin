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

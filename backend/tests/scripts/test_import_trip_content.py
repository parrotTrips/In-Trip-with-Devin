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

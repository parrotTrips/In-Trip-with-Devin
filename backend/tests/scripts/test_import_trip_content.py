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

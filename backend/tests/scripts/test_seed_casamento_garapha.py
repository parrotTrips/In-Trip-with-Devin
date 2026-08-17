import sys
from datetime import UTC, datetime
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts import seed_casamento_garapha as script


def test_trip_data_matches_wedding_request():
    assert script.TRIP_UUID == "CASAMENTO-GARAPHA-2026"
    assert script.TRIP["title"] == "Casamento Gabriela e Raphael"
    assert script.TRIP["start_date"] == "2026-09-04"
    assert script.TRIP["end_date"] == "2026-09-06"
    assert script.TRIP["destination"] == "Prea, Ceara, Brasil"


def test_travelers_are_the_couple_with_normalized_phones():
    assert script.TRAVELERS == [
        {
            "full_name": "Gabriela",
            "preferred_name": "Gabriela",
            "phone": "+5534991825752",
            "email": "",
        },
        {
            "full_name": "Raphael",
            "preferred_name": "Raphael",
            "phone": "+5511993741189",
            "email": "",
        },
    ]


def test_build_dry_run_summary_reports_minimal_changes():
    summary = script.build_dry_run_summary()

    assert summary == {
        "trip_uuid": "CASAMENTO-GARAPHA-2026",
        "would_create_or_update": {
            "wetravel_trips": 1,
            "trip_settings": 1,
            "users": 2,
            "trip_travelers": 2,
            "traveler_profiles": 2,
            "traveler_products": 2,
            "sheet_trip_rows": 1,
            "sheet_traveler_rows": 2,
        },
    }


def test_default_output_dir_is_under_backend_outputs():
    assert script.DEFAULT_OUTPUT_DIR == script.BACKEND_ROOT / "outputs/casamento-garapha"


def test_build_wetravel_trip_record_matches_real_sync_schema():
    now = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)

    record = script.build_wetravel_trip_record(now)

    assert record["entity_key"] == script.TRIP_UUID
    assert record["trip_uuid"] == script.TRIP_UUID
    assert record["trip_id"] == script.TRIP_UUID
    assert record["event_type"] == "manual_seed"
    assert record["currency"] == "BRL"
    assert record["listing_status"] == "manual"
    assert record["published"] == "true"
    assert record["inserted_at"] == now
    assert record["row_updated_at"] == now
    assert "updated_at" not in record


def test_build_sheet_rows_uses_trip_uuid_and_traveler_ids():
    seeded = [
        {
            **script.TRAVELERS[0],
            "user_id": "user-gabriela",
            "trip_traveler_id": "tt-gabriela",
        },
        {
            **script.TRAVELERS[1],
            "user_id": "user-raphael",
            "trip_traveler_id": "tt-raphael",
        },
    ]

    rows = script.build_sheet_rows(seeded)

    assert rows["Viagens"] == [[
        "CASAMENTO-GARAPHA-2026",
        "Casamento Gabriela e Raphael",
        "2026-09-04",
        "2026-09-06",
        "",
    ]]
    assert rows[script.AUDIT_TAB][0][:5] == [
        "CASAMENTO-GARAPHA-2026",
        "Gabriela",
        "Gabriela",
        "+5534991825752",
        "",
    ]
    assert rows[script.AUDIT_TAB][1][9:11] == ["user-raphael", "tt-raphael"]


def test_row_matches_trip_uuid_uses_header_position():
    header = ["phone", "trip_uuid", "name"]

    assert script.row_matches_trip_uuid(["+55", script.TRIP_UUID, "Gabriela"], header)
    assert not script.row_matches_trip_uuid(["+55", "OTHER", "Gabriela"], header)

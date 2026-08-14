import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts import seed_parrot_test_travelers as script


def test_dataset_has_20_fictitious_unique_travelers():
    travelers = script.TEST_TRAVELERS

    assert len(travelers) == 20
    assert len({traveler["phone"] for traveler in travelers}) == 20
    assert len({traveler["email"] for traveler in travelers}) == 20
    assert all(traveler["email"].endswith("@example.com") for traveler in travelers)
    assert all(traveler["phone"].startswith("+15550102") for traveler in travelers)


def test_dataset_has_package_and_profile_data_for_every_traveler():
    for traveler in script.TEST_TRAVELERS:
        assert traveler["full_name"]
        assert traveler["preferred_name"]
        assert traveler["package_name"].startswith("Rio Test Package")
        assert traveler["room_type"] in {"Single Room", "Double Room", "Twin Shared Room"}
        assert traveler["paid_amount_usd"] > 0
        assert "passport_number" in traveler["profile"]


def test_restricted_activity_allowlists_are_subsets_not_everyone():
    allowlists = script.build_restricted_activity_allowlists(script.TEST_TRAVELERS)

    assert set(allowlists) == {
        "Internal Parrot Ops Briefing",
        "Sugarloaf Sunset Test",
        "Restricted Boat Boarding",
    }
    assert len(allowlists["Internal Parrot Ops Briefing"]) == 8
    assert len(allowlists["Sugarloaf Sunset Test"]) == 12
    assert len(allowlists["Restricted Boat Boarding"]) == 7
    assert all(len(phones) < len(script.TEST_TRAVELERS) for phones in allowlists.values())


def test_qr_filename_is_stable_and_safe():
    first = script.TEST_TRAVELERS[0]

    assert script.qr_filename(first) == "parrot-test-01-lara-mendes.png"


def test_managed_sheet_headers_match_import_parsers():
    roteiro = script.MANAGED_HEADERS["Roteiro"]

    assert "atividade_preco_brl" in roteiro
    assert "atividade_endereco" in roteiro
    assert "atividade_max_scans" in roteiro
    assert "max_scans" not in roteiro


def test_trip_uuid_column_is_discovered_from_header_not_assumed_first():
    staff_header = script.MANAGED_HEADERS["Staff"]
    row_for_target = ["+15550000001", "Name", "Role", script.TRIP_UUID]
    row_for_other = ["+15550000002", "Name", "Role", "OTHER-TRIP"]

    assert script.row_matches_trip_uuid(row_for_target, staff_header)
    assert not script.row_matches_trip_uuid(row_for_other, staff_header)


def test_content_managed_headers_include_all_apps_script_import_tabs():
    assert "FAQ" in script.MANAGED_HEADERS
    assert "Cancellation Policy" in script.MANAGED_HEADERS
    assert script.MANAGED_HEADERS["FAQ"] == ["trip_uuid", "question", "answer", "sort_order"]
    assert script.MANAGED_HEADERS["Cancellation Policy"] == ["trip_uuid", "title", "body", "sort_order"]

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


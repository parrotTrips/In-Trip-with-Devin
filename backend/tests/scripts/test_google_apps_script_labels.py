from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONTENT_SCRIPT = PROJECT_ROOT / "google-apps-script" / "Code.gs"
STAFF_SCRIPT = PROJECT_ROOT / "google-apps-script" / "CodeStaff.gs"


def test_content_apps_script_uses_import_for_app_to_sheet_and_export_for_sheet_to_app():
    source = CONTENT_SCRIPT.read_text(encoding="utf-8")

    assert "Import Trips from App" in source
    assert "Export Trip Content to App" in source
    assert "Export Emergency Contacts to App" in source
    assert "Import Trip Content → Supabase" not in source
    assert "run Import Trip Content" not in source
    assert "Sync Trips from App" not in source


def test_staff_apps_script_uses_export_for_sheet_to_app_actions():
    source = STAFF_SCRIPT.read_text(encoding="utf-8")

    assert "Import Trips from App" in source
    assert "Export Staff to App" in source
    assert "Export Contacts to App" in source
    assert "Export Staff Tasks to App" in source
    assert "Export Activity Participants to App" in source
    assert "Import Staff → Supabase" not in source
    assert "Import Contacts → Supabase" not in source
    assert "Sync Trips from Supabase" not in source

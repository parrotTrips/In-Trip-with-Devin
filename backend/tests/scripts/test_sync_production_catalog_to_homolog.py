import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts import sync_production_catalog_to_homolog as script


def test_contract_allowlists_catalog_and_three_validators():
    assert script.VALIDATOR_EMAILS == (
        "angelo@parrottrips.com",
        "sanches@parrottrips.com",
        "becker@parrottrips.com",
    )
    assert script.CATALOG_TABLES == (
        "wetravel_trips",
        "trip_settings",
        "trip_phases",
        "trip_phase_checklist_items",
        "trip_phase_links",
        "trip_activities",
        "trip_contacts",
        "trip_emergency_contacts",
        "trip_recommendations",
        "trip_faqs",
        "trip_cancellation_policies",
    )
    forbidden = {
        "users", "traveler_profiles", "otp_codes",
        "webhook_events", "wetravel_payments", "trip_announcements",
        "staff_tasks",
    }
    assert forbidden.isdisjoint(script.CATALOG_TABLES)
    assert (forbidden - {"users"}).issubset(script.EXCLUDED_TABLES)
    assert "users" in script.TARGET_ONLY_TABLES
    assert "trip_travelers" in script.TARGET_ONLY_TABLES


def test_parse_args_is_dry_run_by_default():
    args = script.parse_args([
        "--production-database-url", "postgresql://one/prod",
        "--homologation-database-url", "postgresql://two/homolog",
    ])
    assert args.execute is False


@pytest.mark.parametrize("missing", ["production", "homologation"])
def test_validate_urls_rejects_missing_url(missing):
    production = "" if missing == "production" else "postgresql://one/prod"
    homologation = "" if missing == "homologation" else "postgresql://two/homolog"
    with pytest.raises(ValueError, match="required"):
        script.validate_database_urls(production, homologation)


def test_validate_urls_rejects_same_database_across_driver_prefixes():
    with pytest.raises(ValueError, match="different databases"):
        script.validate_database_urls(
            "postgresql+asyncpg://user:secret@host/db",
            "postgresql://user:secret@host/db",
        )


def test_order_phases_places_parents_before_children():
    parent = uuid.uuid4()
    child = uuid.uuid4()
    grandchild = uuid.uuid4()
    rows = [
        {"id": grandchild, "parent_phase_id": child},
        {"id": child, "parent_phase_id": parent},
        {"id": parent, "parent_phase_id": None},
    ]
    assert [row["id"] for row in script.order_phase_rows(rows)] == [
        parent, child, grandchild,
    ]


def test_order_phases_rejects_missing_parent():
    with pytest.raises(ValueError, match="missing parent"):
        script.order_phase_rows([
            {"id": uuid.uuid4(), "parent_phase_id": uuid.uuid4()},
        ])


def test_validate_validators_requires_exact_active_staff_records():
    valid = [
        {"email": email, "status": "active", "role": "staff"}
        for email in script.VALIDATOR_EMAILS
    ]
    script.validate_validator_rows(valid)

    with pytest.raises(ValueError, match="exactly one"):
        script.validate_validator_rows(valid[:-1])

    invalid = [dict(row) for row in valid]
    invalid[0]["role"] = "traveler"
    with pytest.raises(ValueError, match="active staff"):
        script.validate_validator_rows(invalid)


def test_memberships_are_deterministic_and_complete():
    users = [{"id": uuid.uuid4()}, {"id": uuid.uuid4()}, {"id": uuid.uuid4()}]
    trips = ["trip-a", "trip-b"]
    first = script.build_staff_memberships(users, trips)
    second = script.build_staff_memberships(users, trips)
    assert [row["id"] for row in first] == [row["id"] for row in second]
    assert len(first) == 6
    assert {(row["wetravel_trip_uuid"], row["user_id"]) for row in first} == {
        (trip, user["id"]) for trip in trips for user in users
    }
    traveler_rows = script.build_base_memberships(users, trips)
    assert len(traveler_rows) == 6
    assert {(row["wetravel_trip_uuid"], row["user_id"]) for row in traveler_rows} == {
        (trip, user["id"]) for trip in trips for user in users
    }


def test_wetravel_rows_drop_webhook_reference():
    rows = [{"id": "one", "source_event_id": "production-event", "title": "Trip"}]
    sanitized = script.sanitize_catalog_rows("wetravel_trips", rows)
    assert sanitized[0]["source_event_id"] is None
    assert sanitized[0]["title"] == "Trip"
    assert rows[0]["source_event_id"] == "production-event"


def test_makefile_exposes_separate_dry_run_and_execute_targets():
    makefile = (BACKEND_ROOT.parent / "Makefile").read_text()
    assert "sync-homolog-catalog-dry-run:" in makefile
    assert "sync-homolog-catalog-execute:" in makefile
    dry_run_recipe = makefile.split("sync-homolog-catalog-dry-run:", 1)[1].split(
        "sync-homolog-catalog-execute:", 1
    )[0]
    execute_recipe = makefile.split("sync-homolog-catalog-execute:", 1)[1]
    assert "--execute" not in dry_run_recipe
    assert "--execute" in execute_recipe


def test_target_schema_allows_known_optional_tables_to_differ():
    actual = set(script.CATALOG_TABLES) | set(script.TARGET_ONLY_TABLES) | {
        "alembic_version", "activity_media", "media_assets", "otp_codes"
    }
    assert script.validate_target_schema(actual) == actual - {"alembic_version"}


def test_target_schema_rejects_missing_required_or_unknown_tables():
    required = set(script.CATALOG_TABLES) | set(script.TARGET_ONLY_TABLES) | {
        "alembic_version"
    }
    with pytest.raises(ValueError, match="missing required"):
        script.validate_target_schema(required - {"users"})
    with pytest.raises(ValueError, match="unknown"):
        script.validate_target_schema(required | {"surprise_table"})


def test_project_rows_uses_target_columns_and_rejects_missing_required_values():
    columns = [
        {"column_name": "trip_uuid", "is_nullable": "NO", "column_default": None},
        {"column_name": "title", "is_nullable": "YES", "column_default": None},
        {"column_name": "updated_at", "is_nullable": "YES", "column_default": None},
    ]
    assert script.project_rows_to_target(
        "wetravel_trips",
        [{"id": "production-only", "trip_uuid": "trip-1", "title": "Trip"}],
        columns,
    ) == [{"trip_uuid": "trip-1", "title": "Trip"}]

    with pytest.raises(ValueError, match="required target column"):
        script.project_rows_to_target(
            "wetravel_trips", [{"title": "Missing UUID"}], columns
        )


@pytest.mark.parametrize(
    ("value", "data_type", "expected"),
    [
        ("2026-09-04", "date", date(2026, 9, 4)),
        ("2026-09-04T10:30:00+00:00", "timestamp with time zone", datetime(2026, 9, 4, 10, 30, tzinfo=timezone.utc)),
        ("12.50", "numeric", Decimal("12.50")),
        ("7", "integer", 7),
        ("true", "boolean", True),
        ("false", "boolean", False),
    ],
)
def test_coerce_value_uses_target_postgres_type(value, data_type, expected):
    assert script.coerce_value(value, data_type) == expected


def test_project_rows_coerces_values_using_target_metadata():
    columns = [
        {"column_name": "trip_uuid", "is_nullable": "NO", "column_default": None, "data_type": "text"},
        {"column_name": "start_date", "is_nullable": "YES", "column_default": None, "data_type": "date"},
    ]
    rows = script.project_rows_to_target(
        "wetravel_trips",
        [{"trip_uuid": "trip-1", "start_date": "2026-09-04"}],
        columns,
    )
    assert rows == [{"trip_uuid": "trip-1", "start_date": date(2026, 9, 4)}]

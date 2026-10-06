#!/usr/bin/env python3
"""Copy the non-personal production trip catalog into homologation safely."""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Iterable, Sequence
from urllib.parse import urlsplit

import asyncpg


VALIDATOR_EMAILS = (
    "angelo@parrottrips.com",
    "sanches@parrottrips.com",
    "becker@parrottrips.com",
)

CATALOG_TABLES = (
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

EXCLUDED_TABLES = frozenset({
    "activity_checkin_scan_events",
    "activity_checkins",
    "activity_participants",
    "otp_codes",
    "sheet_sync_jobs",
    "staff_tasks",
    "transfer_cancel_requests",
    "traveler_app_feedback",
    "traveler_checklist_progress",
    "traveler_phase_progress",
    "traveler_products",
    "traveler_profiles",
    "trip_announcement_reads",
    "trip_announcements",
    "webhook_events",
    "wetravel_bookings",
    "wetravel_leads",
    "wetravel_order_options",
    "wetravel_participant_phones",
    "wetravel_payments",
    "wetravel_transactions",
})

TARGET_ONLY_TABLES = ("users", "trip_travelers", "trip_staff")
TARGET_EMPTY_TABLES = frozenset({"activity_media", "media_assets"})
EXPECTED_PUBLIC_TABLES = frozenset(CATALOG_TABLES) | EXCLUDED_TABLES | TARGET_EMPTY_TABLES | frozenset(
    TARGET_ONLY_TABLES
) | {"alembic_version"}
STAFF_NAMESPACE = uuid.UUID("3105f0ad-cc86-4fa9-bb1e-52111de99b86")
BASE_MEMBERSHIP_NAMESPACE = uuid.UUID("b16165ed-80dc-4e8d-88c7-4eae242649eb")


@dataclass(frozen=True)
class CatalogSnapshot:
    tables: dict[str, list[dict[str, Any]]]
    validators: list[dict[str, Any]]
    trip_uuids: tuple[str, ...]

    @property
    def counts(self) -> dict[str, int]:
        return {table: len(self.tables[table]) for table in CATALOG_TABLES}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production-database-url", required=True)
    parser.add_argument("--homologation-database-url", required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Write to homologation. Without this flag the command is read-only.",
    )
    return parser.parse_args(argv)


def normalize_asyncpg_url(value: str) -> str:
    return value.replace("postgresql+asyncpg://", "postgresql://", 1).replace(
        "postgresql+psycopg2://", "postgresql://", 1
    )


def _database_identity(value: str) -> tuple[str | None, str | None, int | None, str]:
    parsed = urlsplit(normalize_asyncpg_url(value))
    return parsed.username, parsed.hostname, parsed.port, parsed.path.rstrip("/")


def validate_database_urls(production: str, homologation: str) -> tuple[str, str]:
    if not production or not homologation:
        raise ValueError("Both database URLs are required")
    production_url = normalize_asyncpg_url(production)
    homologation_url = normalize_asyncpg_url(homologation)
    if _database_identity(production_url) == _database_identity(homologation_url):
        raise ValueError("Production and homologation must be different databases")
    return production_url, homologation_url


def order_phase_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = {row["id"]: dict(row) for row in rows}
    known_ids = set(remaining)
    missing = {
        row["parent_phase_id"]
        for row in remaining.values()
        if row.get("parent_phase_id") is not None
        and row["parent_phase_id"] not in known_ids
    }
    if missing:
        raise ValueError("Trip phase references a missing parent")

    ordered: list[dict[str, Any]] = []
    inserted: set[Any] = set()
    while remaining:
        ready = [
            row for row in remaining.values()
            if row.get("parent_phase_id") is None
            or row["parent_phase_id"] in inserted
        ]
        if not ready:
            raise ValueError("Trip phase hierarchy contains a cycle")
        ready.sort(key=lambda row: (row.get("sort_order", 0), str(row["id"])))
        for row in ready:
            ordered.append(row)
            inserted.add(row["id"])
            del remaining[row["id"]]
    return ordered


def validate_validator_rows(rows: Sequence[dict[str, Any]]) -> None:
    by_email: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_email.setdefault(str(row.get("email", "")).lower(), []).append(row)
    for email in VALIDATOR_EMAILS:
        matches = by_email.get(email, [])
        if len(matches) != 1:
            raise ValueError(f"Validator {email} must have exactly one source record")
        if matches[0].get("status") != "active" or matches[0].get("role") != "staff":
            raise ValueError(f"Validator {email} must be active staff")


def sanitize_catalog_rows(
    table: str, rows: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    copied = [dict(row) for row in rows]
    if table == "wetravel_trips":
        for row in copied:
            row["source_event_id"] = None
    if table == "trip_phases":
        return order_phase_rows(copied)
    return copied


def build_staff_memberships(
    users: Sequence[dict[str, Any]], trip_uuids: Iterable[str]
) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    result: list[dict[str, Any]] = []
    for trip_uuid in sorted(set(trip_uuids)):
        for user in sorted(users, key=lambda row: str(row["id"])):
            user_id = user["id"]
            membership_id = uuid.uuid5(STAFF_NAMESPACE, f"{trip_uuid}:{user_id}")
            result.append({
                "id": membership_id,
                "wetravel_trip_uuid": trip_uuid,
                "user_id": user_id,
                "function": "Staff",
                "photo_url": None,
                "bio": None,
                "created_at": now,
                "updated_at": now,
            })
    return result


def build_base_memberships(
    users: Sequence[dict[str, Any]], trip_uuids: Iterable[str]
) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    result: list[dict[str, Any]] = []
    for trip_uuid in sorted(set(trip_uuids)):
        for user in sorted(users, key=lambda row: str(row["id"])):
            user_id = user["id"]
            result.append({
                "id": uuid.uuid5(BASE_MEMBERSHIP_NAMESPACE, f"{trip_uuid}:{user_id}"),
                "wetravel_trip_uuid": trip_uuid,
                "user_id": user_id,
                "created_at": now,
                "updated_at": now,
            })
    return result


async def _public_tables(connection: asyncpg.Connection) -> set[str]:
    rows = await connection.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    )
    return {row["tablename"] for row in rows}


def validate_target_schema(actual_tables: set[str]) -> set[str]:
    required = frozenset(CATALOG_TABLES) | frozenset(TARGET_ONLY_TABLES) | {
        "alembic_version"
    }
    missing = required - actual_tables
    unknown = actual_tables - EXPECTED_PUBLIC_TABLES
    if missing or unknown:
        raise ValueError(
            "Homologation schema mismatch; "
            f"missing required={sorted(missing)}, unknown={sorted(unknown)}"
        )
    return actual_tables - {"alembic_version"}


async def _read_table(
    connection: asyncpg.Connection, table: str
) -> list[dict[str, Any]]:
    if table not in EXPECTED_PUBLIC_TABLES:
        raise ValueError(f"Table is not allowlisted: {table}")
    return [dict(row) for row in await connection.fetch(f'SELECT * FROM "{table}"')]


def project_rows_to_target(
    table: str,
    rows: Sequence[dict[str, Any]],
    target_columns: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not rows:
        return []
    source_columns = set(rows[0])
    selected = [
        column["column_name"]
        for column in target_columns
        if column["column_name"] in source_columns
    ]
    required = {
        column["column_name"]
        for column in target_columns
        if column["is_nullable"] == "NO" and column.get("column_default") is None
    }
    missing = required - set(selected)
    if missing:
        raise ValueError(
            f"{table} is missing required target column(s): {sorted(missing)}"
        )
    types = {
        column["column_name"]: column.get("data_type", "text")
        for column in target_columns
    }
    projected = [
        {
            column: coerce_value(row[column], types[column])
            for column in selected
        }
        for row in rows
    ]
    for row in projected:
        null_required = {column for column in required if row.get(column) is None}
        if null_required:
            raise ValueError(
                f"{table} has null required target column(s): {sorted(null_required)}"
            )
    return projected


def coerce_value(value: Any, data_type: str) -> Any:
    if value is None:
        return None
    if data_type == "date":
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value)[:10])
    if data_type in {"timestamp with time zone", "timestamp without time zone"}:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if data_type == "uuid":
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    if data_type in {"numeric", "decimal"}:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    if data_type in {"smallint", "integer", "bigint"}:
        return int(value)
    if data_type in {"real", "double precision"}:
        return float(value)
    if data_type == "boolean":
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "t", "1", "yes"}:
            return True
        if normalized in {"false", "f", "0", "no"}:
            return False
        raise ValueError(f"Invalid boolean value: {value!r}")
    if data_type in {"json", "jsonb"} and not isinstance(value, str):
        return json.dumps(value, default=str)
    return value


async def _target_columns(
    connection: asyncpg.Connection, table: str
) -> list[dict[str, Any]]:
    rows = await connection.fetch(
        """
        SELECT column_name, is_nullable, column_default, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = $1
        ORDER BY ordinal_position
        """,
        table,
    )
    return [dict(row) for row in rows]


async def read_source_snapshot(connection: asyncpg.Connection) -> CatalogSnapshot:
    actual_tables = await _public_tables(connection)
    missing = set(CATALOG_TABLES) - actual_tables
    if missing:
        raise ValueError(f"Production is missing catalog tables: {sorted(missing)}")

    tables: dict[str, list[dict[str, Any]]] = {}
    for table in CATALOG_TABLES:
        tables[table] = sanitize_catalog_rows(
            table, await _read_table(connection, table)
        )

    validators = [dict(row) for row in await connection.fetch(
        "SELECT * FROM users WHERE lower(email) = ANY($1::text[])",
        list(VALIDATOR_EMAILS),
    )]
    validate_validator_rows(validators)

    trip_uuids = tuple(sorted({
        str(row["trip_uuid"])
        for row in tables["wetravel_trips"]
        if row.get("trip_uuid")
    }))
    if not trip_uuids:
        raise ValueError("Production catalog contains no trip UUIDs")
    return CatalogSnapshot(tables, validators, trip_uuids)


async def _insert_rows(
    connection: asyncpg.Connection,
    table: str,
    rows: Sequence[dict[str, Any]],
) -> None:
    if not rows:
        return
    if table not in EXPECTED_PUBLIC_TABLES:
        raise ValueError(f"Table is not allowlisted: {table}")
    columns = list(rows[0])
    if any(list(row) != columns for row in rows):
        raise ValueError(f"Inconsistent columns for {table}")
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    placeholders = ", ".join(f"${index}" for index in range(1, len(columns) + 1))
    values = [tuple(row[column] for column in columns) for row in rows]
    await connection.executemany(
        f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})',
        values,
    )


async def rebuild_homologation(
    connection: asyncpg.Connection, snapshot: CatalogSnapshot
) -> dict[str, int]:
    actual_tables = await _public_tables(connection)
    data_tables = sorted(validate_target_schema(actual_tables))
    quoted = ", ".join(f'"{table}"' for table in data_tables)
    async with connection.transaction():
        await connection.execute(f"TRUNCATE TABLE {quoted} CASCADE")
        for table in CATALOG_TABLES:
            rows = project_rows_to_target(
                table, snapshot.tables[table], await _target_columns(connection, table)
            )
            await _insert_rows(connection, table, rows)
        validator_rows = project_rows_to_target(
            "users", snapshot.validators, await _target_columns(connection, "users")
        )
        await _insert_rows(connection, "users", validator_rows)
        base_memberships = build_base_memberships(snapshot.validators, snapshot.trip_uuids)
        base_membership_rows = project_rows_to_target(
            "trip_travelers",
            base_memberships,
            await _target_columns(connection, "trip_travelers"),
        )
        await _insert_rows(connection, "trip_travelers", base_membership_rows)
        memberships = build_staff_memberships(snapshot.validators, snapshot.trip_uuids)
        membership_rows = project_rows_to_target(
            "trip_staff", memberships, await _target_columns(connection, "trip_staff")
        )
        await _insert_rows(connection, "trip_staff", membership_rows)

        user_count = await connection.fetchval("SELECT count(*) FROM users")
        non_staff_count = await connection.fetchval(
            "SELECT count(*) FROM users WHERE role <> 'staff' OR status <> 'active'"
        )
        membership_count = await connection.fetchval("SELECT count(*) FROM trip_staff")
        base_membership_count = await connection.fetchval(
            "SELECT count(*) FROM trip_travelers"
        )
        expected_memberships = len(snapshot.trip_uuids) * len(VALIDATOR_EMAILS)
        if user_count != len(VALIDATOR_EMAILS) or non_staff_count != 0:
            raise ValueError("Homologation user invariant failed")
        if membership_count != expected_memberships or base_membership_count != expected_memberships:
            raise ValueError("Homologation staff membership invariant failed")
        for table, expected in snapshot.counts.items():
            actual = await connection.fetchval(f'SELECT count(*) FROM "{table}"')
            if actual != expected:
                raise ValueError(f"Catalog count invariant failed for {table}")
        for table in (EXCLUDED_TABLES | TARGET_EMPTY_TABLES) & actual_tables:
            actual = await connection.fetchval(f'SELECT count(*) FROM "{table}"')
            if actual:
                raise ValueError(f"Excluded table is not empty: {table}")

    return {
        **snapshot.counts,
        "users": len(snapshot.validators),
        "trip_travelers": len(snapshot.trip_uuids) * len(snapshot.validators),
        "trip_staff": len(snapshot.trip_uuids) * len(snapshot.validators),
    }


def _print_summary(mode: str, snapshot: CatalogSnapshot, result: dict[str, int] | None = None) -> None:
    payload = {
        "mode": mode,
        "trip_count": len(snapshot.trip_uuids),
        "validator_count": len(snapshot.validators),
        "catalog_counts": snapshot.counts,
    }
    if result is not None:
        payload["homologation_counts"] = result
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


async def run(args: argparse.Namespace) -> None:
    production_url, homologation_url = validate_database_urls(
        args.production_database_url, args.homologation_database_url
    )
    production = await asyncpg.connect(production_url, timeout=30)
    try:
        async with production.transaction(readonly=True):
            snapshot = await read_source_snapshot(production)
    finally:
        await production.close()

    if not args.execute:
        _print_summary("dry-run", snapshot)
        return

    homologation = await asyncpg.connect(homologation_url, timeout=30)
    try:
        result = await rebuild_homologation(homologation, snapshot)
    finally:
        await homologation.close()
    _print_summary("execute", snapshot, result)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

"""Integration tests for write_to_db against a real Postgres schema."""

import sys
import uuid
from pathlib import Path

import asyncpg
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_trip_content import Activity, InTripDay, write_to_db

TRIP_UUID = "TEST-WRITE-DB"


def _pg_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


async def _seed_trip_with_scan_event(conn: asyncpg.Connection) -> tuple[str, str]:
    """Create one phase + activity for the trip, plus a scan event referencing it."""
    phase_id = str(uuid.uuid4())
    activity_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    await conn.execute(
        """
        INSERT INTO trip_phases
            (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
             short_description, detailed_description, sort_order,
             is_locked_by_default, is_visible, created_at, updated_at)
        VALUES ($1, $2, 'in-trip', 'Day 1', '', '', '', '', 0, false, true, now(), now())
        """,
        phase_id, TRIP_UUID,
    )
    await conn.execute(
        """
        INSERT INTO trip_activities
            (id, trip_phase_id, name, activity_type, short_description,
             practical_info, sort_order, created_at, updated_at)
        VALUES ($1, $2, 'Sugarloaf', 'included', '', '', 0, now(), now())
        """,
        activity_id, phase_id,
    )
    await conn.execute(
        "INSERT INTO users (id, phone, status, role, created_at, updated_at) "
        "VALUES ($1, '+5511999999999', 'active', 'staff', now(), now())",
        user_id,
    )
    await conn.execute(
        """
        INSERT INTO activity_checkin_scan_events
            (id, trip_activity_id, scanned_by_user_id, status, created_at)
        VALUES ($1, $2, $3, 'success', now())
        """,
        str(uuid.uuid4()), activity_id, user_id,
    )
    return phase_id, activity_id


@pytest.mark.asyncio
async def test_write_to_db_unlinks_scan_events_from_deleted_activities(database_url):
    """Reimporting content must not fail on the scan-events FK, and must keep the audit rows."""
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        _, old_activity_id = await _seed_trip_with_scan_event(conn)

        fresh_day = InTripDay(
            dia=1, data="2026-08-24", title="Day 1", subtitle="", icon="",
            short_description="", detailed_description="",
            activities=[Activity(
                name="Corcovado", activity_type="included", horario="08:00",
                starts_at=None, duration_minutes=60, short_description="",
                practical_info="", address=None, max_checkins=1,
                amount_brl=None, sort_order=0,
            )],
        )

        await write_to_db(conn, TRIP_UUID, [], [fresh_day])

        assert await conn.fetchval(
            "SELECT count(*) FROM activity_checkin_scan_events"
        ) == 1, "scan event audit row must be preserved"
        assert await conn.fetchval(
            "SELECT trip_activity_id FROM activity_checkin_scan_events"
        ) is None, "scan event must be unlinked from the deleted activity"
        assert await conn.fetchval(
            "SELECT count(*) FROM trip_activities WHERE id = $1", uuid.UUID(old_activity_id)
        ) == 0, "old activity must be gone"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_admin_reset_content_unlinks_scan_events_and_clears_checkins(
    database_url, monkeypatch
):
    """Clearing trip content must not fail on activity child-table FKs."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    sys.modules.pop("app.services.admin_service", None)
    from app.services.admin_service import admin_reset_content

    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        await _seed_trip_with_scan_event(conn)
    finally:
        await conn.close()

    await admin_reset_content(TRIP_UUID)

    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        assert await conn.fetchval("SELECT count(*) FROM trip_phases") == 0
        assert await conn.fetchval("SELECT count(*) FROM trip_activities") == 0
        assert await conn.fetchval(
            "SELECT count(*) FROM activity_checkin_scan_events"
        ) == 1, "scan event audit row must be preserved"
        assert await conn.fetchval(
            "SELECT trip_activity_id FROM activity_checkin_scan_events"
        ) is None
    finally:
        await conn.close()

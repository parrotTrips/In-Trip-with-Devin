"""Tests for the read-only multi-trip membership audit script.

Run against a real (ephemeral, per-test) Postgres via the `database_url` fixture —
never a real/remote database. The script itself must never be run outside tests
against anything but a URL explicitly supplied on the command line.
"""

import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import asyncpg
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.audit_multi_trip_memberships import (
    format_report,
    find_duplicate_normalized_phones,
    find_memberships_with_missing_trip,
    find_staff_missing_traveler_link,
    find_unnormalized_phones,
    find_users_with_multiple_eligible_trips,
    find_users_with_role_staff_missing_trip_staff,
    normalize_phone_digits,
    parse_args,
    run_audit,
)


def _pg_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


async def _insert_user(conn: asyncpg.Connection, phone: str, *, role: str = "traveler") -> str:
    return await conn.fetchval(
        """
        insert into users (id, phone, status, role, created_at, updated_at)
        values ($1, $2, 'active', $3, now(), now())
        returning id
        """,
        uuid.uuid4(),
        phone,
        role,
    )


async def _insert_trip(
    conn: asyncpg.Connection, trip_uuid: str, *, end_date: date | None
) -> None:
    await conn.execute(
        """
        insert into wetravel_trips (trip_uuid, title, destination, start_date, end_date)
        values ($1, $2, 'Brazil', $3, $4)
        on conflict (trip_uuid) do nothing
        """,
        trip_uuid,
        f"Title {trip_uuid}",
        date(2027, 1, 1),
        end_date,
    )


async def _insert_trip_traveler(conn: asyncpg.Connection, trip_uuid: str, user_id: str) -> str:
    return await conn.fetchval(
        """
        insert into trip_travelers (id, wetravel_trip_uuid, user_id, created_at, updated_at)
        values ($1, $2, $3, now(), now())
        returning id
        """,
        uuid.uuid4(),
        trip_uuid,
        user_id,
    )


async def _insert_trip_staff(conn: asyncpg.Connection, trip_uuid: str, user_id: str) -> str:
    return await conn.fetchval(
        """
        insert into trip_staff (id, wetravel_trip_uuid, user_id, created_at, updated_at)
        values ($1, $2, $3, now(), now())
        returning id
        """,
        uuid.uuid4(),
        trip_uuid,
        user_id,
    )


def test_normalize_phone_digits_strips_all_non_digits():
    assert normalize_phone_digits("+55 (11) 99999-0001") == "5511999990001"
    assert normalize_phone_digits("5511999990001") == "5511999990001"
    assert normalize_phone_digits(None) == ""


def test_parse_args_requires_database_url():
    with pytest.raises(SystemExit):
        parse_args([])

    args = parse_args(["postgresql://user@host/db"])
    assert args.database_url == "postgresql://user@host/db"


@pytest.mark.asyncio
async def test_find_duplicate_normalized_phones_groups_inconsistent_formatting(database_url):
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        await _insert_user(conn, "+5511990001234")
        await _insert_user(conn, "5511990001234")
        await _insert_user(conn, "+5511990009999")  # unique, not a duplicate

        duplicates = await find_duplicate_normalized_phones(conn)

        assert len(duplicates) == 1
        assert duplicates[0]["normalized_phone"] == "5511990001234"
        assert {u["phone"] for u in duplicates[0]["users"]} == {
            "+5511990001234",
            "5511990001234",
        }
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_find_staff_missing_traveler_link_reports_orphans(database_url):
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        trip_uuid = "audit-trip-orphan-staff"
        await _insert_trip(conn, trip_uuid, end_date=None)
        user_id = await _insert_user(conn, "+5511990002222")
        await _insert_trip_staff(conn, trip_uuid, user_id)
        # Deliberately no trip_travelers row for this (trip, user) pair.

        orphans = await find_staff_missing_traveler_link(conn)

        assert len(orphans) == 1
        assert orphans[0]["trip_uuid"] == trip_uuid
        assert orphans[0]["user_id"] == str(user_id)
        assert orphans[0]["phone"] == "+5511990002222"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_find_staff_missing_traveler_link_is_empty_when_linked(database_url):
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        trip_uuid = "audit-trip-linked-staff"
        await _insert_trip(conn, trip_uuid, end_date=None)
        user_id = await _insert_user(conn, "+5511990003333")
        await _insert_trip_traveler(conn, trip_uuid, user_id)
        await _insert_trip_staff(conn, trip_uuid, user_id)

        orphans = await find_staff_missing_traveler_link(conn)

        assert orphans == []
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_find_memberships_with_missing_trip(database_url):
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        user_id = await _insert_user(conn, "+5511990004444")
        # No wetravel_trips row for this trip_uuid at all.
        await _insert_trip_traveler(conn, "audit-trip-does-not-exist", user_id)
        await _insert_trip_staff(conn, "audit-trip-does-not-exist", user_id)

        missing = await find_memberships_with_missing_trip(conn)

        sources = {(m["source"], m["trip_uuid"]) for m in missing}
        assert sources == {
            ("trip_travelers", "audit-trip-does-not-exist"),
            ("trip_staff", "audit-trip-does-not-exist"),
        }
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_find_users_with_multiple_eligible_trips_derives_role_per_trip(database_url):
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        trip_a = "audit-trip-eligible-a"
        trip_b = "audit-trip-eligible-b"
        ended_trip = "audit-trip-ended"

        await _insert_trip(conn, trip_a, end_date=None)
        await _insert_trip(conn, trip_b, end_date=None)
        await _insert_trip(conn, ended_trip, end_date=date.today() - timedelta(days=1))

        mixed_user = await _insert_user(conn, "+5511990005555")
        await _insert_trip_traveler(conn, trip_a, mixed_user)
        await _insert_trip_traveler(conn, trip_b, mixed_user)
        await _insert_trip_staff(conn, trip_b, mixed_user)
        # Membership on an ended trip must not count toward "multiple eligible".
        await _insert_trip_traveler(conn, ended_trip, mixed_user)

        single_trip_user = await _insert_user(conn, "+5511990006666")
        await _insert_trip_traveler(conn, trip_a, single_trip_user)

        multi = await find_users_with_multiple_eligible_trips(conn)

        assert len(multi) == 1
        entry = multi[0]
        assert entry["user_id"] == str(mixed_user)
        roles_by_trip = {t["trip_uuid"]: t["role"] for t in entry["trips"]}
        assert roles_by_trip == {trip_a: "traveler", trip_b: "staff"}
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_find_users_with_role_staff_missing_trip_staff_reports_deploy_time_loss(
    database_url,
):
    """A `users.role = 'staff'` account with an eligible trip membership but no
    matching `trip_staff` row for that trip lost staff access when the old
    global-role model was retired — this must be flagged so it can be backfilled
    before enabling the new flow.
    """
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        trip_a = "audit-trip-role-staff-a"
        trip_b = "audit-trip-role-staff-b"
        ended_trip = "audit-trip-role-staff-ended"
        await _insert_trip(conn, trip_a, end_date=None)
        await _insert_trip(conn, trip_b, end_date=None)
        await _insert_trip(conn, ended_trip, end_date=date.today() - timedelta(days=1))

        # Lost staff access on trip_a (no trip_staff row there at all).
        lost_user = await _insert_user(conn, "+5511990011111", role="staff")
        await _insert_trip_traveler(conn, trip_a, lost_user)
        # Also a member of an ended trip — must not be reported for that trip.
        await _insert_trip_traveler(conn, ended_trip, lost_user)

        # Already backfilled: has both users.role='staff' and a trip_staff row.
        backfilled_user = await _insert_user(conn, "+5511990022222", role="staff")
        await _insert_trip_traveler(conn, trip_b, backfilled_user)
        await _insert_trip_staff(conn, trip_b, backfilled_user)

        # Plain traveler: users.role != 'staff', must never be reported.
        traveler_user = await _insert_user(conn, "+5511990033333", role="traveler")
        await _insert_trip_traveler(conn, trip_a, traveler_user)

        report = await find_users_with_role_staff_missing_trip_staff(conn)

        assert len(report) == 1
        entry = report[0]
        assert entry["user_id"] == str(lost_user)
        assert entry["phone"] == "+5511990011111"
        assert entry["trips"] == [trip_a]
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_find_unnormalized_phones_reports_mismatch_with_normalize_phone(database_url):
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        normalized_user = await _insert_user(conn, "+5511990044444")
        messy_user = await _insert_user(conn, "55 (11) 99005-5555")

        report = await find_unnormalized_phones(conn)

        ids = {r["user_id"] for r in report}
        assert str(messy_user) in ids
        assert str(normalized_user) not in ids
        entry = next(r for r in report if r["user_id"] == str(messy_user))
        assert entry["phone"] == "55 (11) 99005-5555"
        assert entry["normalized_phone"] == "+5511990055555"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_run_audit_and_format_report_end_to_end(database_url):
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        trip_uuid = "audit-trip-e2e"
        await _insert_trip(conn, trip_uuid, end_date=None)
        user_id = await _insert_user(conn, "+5511990007777")
        await _insert_trip_staff(conn, trip_uuid, user_id)  # orphaned: no trip_travelers
    finally:
        await conn.close()

    report = await run_audit(database_url)

    assert report["staff_missing_trip_traveler_link"]
    assert report["staff_missing_trip_traveler_link"][0]["trip_uuid"] == trip_uuid
    assert "users_role_staff_missing_trip_staff" in report
    assert "unnormalized_phones" in report

    text = format_report(report)
    assert "Multi-trip membership audit" in text
    assert "trip_staff rows missing a trip_travelers row: 1" in text
    assert trip_uuid in text
    assert "users.role='staff' with an eligible trip but no trip_staff row" in text
    assert "Phones that do not match normalize_phone" in text


@pytest.mark.asyncio
async def test_run_audit_does_not_write_to_the_database(database_url):
    """The audit must be provably read-only: running it must not change row counts."""
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        trip_uuid = "audit-trip-readonly-check"
        await _insert_trip(conn, trip_uuid, end_date=None)
        user_id = await _insert_user(conn, "+5511990008888")
        await _insert_trip_traveler(conn, trip_uuid, user_id)

        before_users = await conn.fetchval("SELECT count(*) FROM users")
        before_travelers = await conn.fetchval("SELECT count(*) FROM trip_travelers")
        before_staff = await conn.fetchval("SELECT count(*) FROM trip_staff")
    finally:
        await conn.close()

    await run_audit(database_url)

    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        after_users = await conn.fetchval("SELECT count(*) FROM users")
        after_travelers = await conn.fetchval("SELECT count(*) FROM trip_travelers")
        after_staff = await conn.fetchval("SELECT count(*) FROM trip_staff")
    finally:
        await conn.close()

    assert (before_users, before_travelers, before_staff) == (
        after_users,
        after_travelers,
        after_staff,
    )


@pytest.mark.asyncio
async def test_readonly_transaction_used_by_run_audit_rejects_writes(database_url):
    """Prove writes are actually impossible, not merely absent: attempting a write
    inside the exact transaction mode `run_audit` uses (`conn.transaction(readonly=
    True)`) must be rejected by Postgres itself, regardless of what queries the
    audit's finder functions happen to run today.
    """
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        with pytest.raises(asyncpg.exceptions.ReadOnlySQLTransactionError):
            async with conn.transaction(readonly=True):
                await conn.execute(
                    "INSERT INTO users (id, phone, status, role, created_at, updated_at)"
                    " VALUES ($1, '+5511990009990', 'active', 'traveler', now(), now())",
                    uuid.uuid4(),
                )

        # The rejected write must not have landed (the failed transaction rolls back).
        count = await conn.fetchval(
            "SELECT count(*) FROM users WHERE phone = $1", "+5511990009990"
        )
        assert count == 0
    finally:
        await conn.close()

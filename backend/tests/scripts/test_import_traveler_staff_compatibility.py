"""Cross-script regression tests: the traveler importer (wedding CSV) and the staff
importer must resolve the same normalized phone number to a single `users` row, with
one `trip_travelers` row per trip and a `trip_staff` row only where the person is
actually staff. Run against a real (ephemeral, per-test) Postgres via the `database_url`
fixture — never a real/remote database.
"""

import sys
from pathlib import Path

import asyncpg
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_casamento_contacts_from_csv import TRIP_UUID as TRAVELER_TRIP_UUID
from scripts.import_casamento_contacts_from_csv import import_contacts
from scripts.import_staff_content import write_staff

STAFF_TRIP_UUID = "TEST-2026-STAFF-COMPAT"


def _pg_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


@pytest.mark.asyncio
async def test_same_person_imported_as_traveler_then_staff_reuses_one_user(database_url):
    """Same normalized phone imported as a traveler on trip A (wedding CSV importer)
    and then as staff on trip B (staff-content importer, with the phone typed without
    a leading "+" as spreadsheets often store it) must resolve to one `users` row, two
    `trip_travelers` rows, and a `trip_staff` row only for trip B.
    """
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        normalized_phone = "+5511990001234"

        traveler_result = await import_contacts(
            conn, [{"name": "Ana Dupla", "phone": normalized_phone, "marker": ""}]
        )
        assert len(traveler_result["inserted"]) == 1

        staff_result = await write_staff(
            conn,
            STAFF_TRIP_UUID,
            [{
                "phone": "5511990001234",  # same number, missing the leading "+"
                "nome": "Ana Dupla",
                "funcao": "Suporte",
                "trip_uuid": STAFF_TRIP_UUID,
                "photo_url": None,
                "bio": None,
            }],
        )
        assert staff_result["created"] == 0, "must reuse the existing user, not create a new one"

        user_rows = await conn.fetch("SELECT id FROM users WHERE phone = $1", normalized_phone)
        assert len(user_rows) == 1, "same person must resolve to a single users row"
        user_id = user_rows[0]["id"]

        trip_traveler_rows = await conn.fetch(
            "SELECT wetravel_trip_uuid FROM trip_travelers WHERE user_id = $1", user_id
        )
        assert {row["wetravel_trip_uuid"] for row in trip_traveler_rows} == {
            TRAVELER_TRIP_UUID,
            STAFF_TRIP_UUID,
        }

        trip_staff_rows = await conn.fetch(
            "SELECT wetravel_trip_uuid FROM trip_staff WHERE user_id = $1", user_id
        )
        assert {row["wetravel_trip_uuid"] for row in trip_staff_rows} == {STAFF_TRIP_UUID}
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_reimporting_staff_is_idempotent(database_url):
    """Running the staff importer twice for the same person/trip must not create
    duplicate `trip_travelers` or `trip_staff` rows."""
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        phone = "+5511990005678"
        member = {
            "phone": phone,
            "nome": "Bruno Repetido",
            "funcao": "Coordenacao",
            "trip_uuid": STAFF_TRIP_UUID,
            "photo_url": None,
            "bio": None,
        }

        first = await write_staff(conn, STAFF_TRIP_UUID, [member])
        second = await write_staff(conn, STAFF_TRIP_UUID, [member])

        assert first["created"] == 1
        assert first["linked"] == 1
        assert second["created"] == 0
        assert second["linked"] == 0, "second import must not re-link an existing membership"

        user_id = await conn.fetchval("SELECT id FROM users WHERE phone = $1", phone)
        trip_traveler_count = await conn.fetchval(
            "SELECT count(*) FROM trip_travelers WHERE user_id = $1 AND wetravel_trip_uuid = $2",
            user_id,
            STAFF_TRIP_UUID,
        )
        trip_staff_count = await conn.fetchval(
            "SELECT count(*) FROM trip_staff WHERE user_id = $1 AND wetravel_trip_uuid = $2",
            user_id,
            STAFF_TRIP_UUID,
        )
        assert trip_traveler_count == 1
        assert trip_staff_count == 1
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_reimporting_traveler_csv_contact_is_idempotent(database_url):
    """Running the wedding CSV importer twice for the same contact skips the second
    import instead of creating a duplicate membership."""
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        contact = {"name": "Carla Repetida", "phone": "+5511990009999", "marker": ""}

        first = await import_contacts(conn, [contact])
        second = await import_contacts(conn, [contact])

        assert len(first["inserted"]) == 1
        assert len(second["inserted"]) == 0
        assert len(second["skipped"]) == 1

        trip_traveler_count = await conn.fetchval(
            "SELECT count(*) FROM trip_travelers tt JOIN users u ON u.id = tt.user_id"
            " WHERE u.phone = $1 AND tt.wetravel_trip_uuid = $2",
            contact["phone"],
            TRAVELER_TRIP_UUID,
        )
        assert trip_traveler_count == 1
    finally:
        await conn.close()

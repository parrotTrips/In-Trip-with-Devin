"""Cross-script regression tests: the traveler importer (wedding CSV) and the staff
importer must resolve the same normalized phone number to a single `users` row, with
one `trip_travelers` row per trip and a `trip_staff` row only where the person is
actually staff. Run against a real (ephemeral, per-test) Postgres via the `database_url`
fixture — never a real/remote database.
"""

import sys
import uuid
from pathlib import Path

import asyncpg
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_casamento_contacts_from_csv import TRIP_UUID as TRAVELER_TRIP_UUID
from scripts.import_casamento_contacts_from_csv import import_contacts
from scripts.import_staff_content import (
    StaffTaskImportError,
    write_activity_participants,
    write_staff,
    write_staff_tasks,
)

STAFF_TRIP_UUID = "TEST-2026-STAFF-COMPAT"
OTHER_TRIP_UUID = "TEST-2026-OTHER-TRIP-COMPAT"


def _pg_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


async def _seed_day_and_activity(
    conn: asyncpg.Connection, trip_uuid: str, activity_name: str, *, dia: int = 1
) -> None:
    """Seed one in-trip day (as the `dia`-th in-trip phase) plus one activity under
    it, matching the shape write_staff_tasks/write_activity_participants expect.
    """
    phase_id = uuid.uuid4()
    await conn.execute(
        """
        INSERT INTO trip_phases
            (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
             short_description, detailed_description, sort_order,
             is_locked_by_default, is_visible, created_at, updated_at)
        VALUES ($1, $2, 'in-trip', 'Day', '', '', '', '', $3, false, true, now(), now())
        """,
        phase_id,
        trip_uuid,
        dia - 1,
    )
    await conn.execute(
        """
        INSERT INTO trip_activities
            (id, trip_phase_id, name, activity_type, short_description,
             practical_info, sort_order, created_at, updated_at)
        VALUES ($1, $2, $3, 'included', '', '', 0, now(), now())
        """,
        uuid.uuid4(),
        phase_id,
        activity_name,
    )


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


@pytest.mark.asyncio
async def test_activity_participant_import_succeeds_for_a_traveler_who_is_staff_elsewhere(
    database_url,
):
    """A person who is staff on trip B must still import successfully as an
    activity participant on trip A, where they are only a plain traveler. The
    participant lookup must be scoped by trip_travelers membership for trip A,
    never by the person's global users.role (which write_staff sets to 'staff'
    once they're staff on any trip).
    """
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        phone = "+5511990001111"
        activity_name = "Passeio de Barco"

        # Traveler membership on trip A (the wedding trip).
        traveler_result = await import_contacts(
            conn, [{"name": "Mixed Role Participant", "phone": phone, "marker": ""}]
        )
        assert len(traveler_result["inserted"]) == 1

        # Staff membership on trip B — sets users.role = 'staff' globally.
        await write_staff(
            conn,
            STAFF_TRIP_UUID,
            [{
                "phone": phone,
                "nome": "Mixed Role Participant",
                "funcao": "Suporte",
                "trip_uuid": STAFF_TRIP_UUID,
                "photo_url": None,
                "bio": None,
            }],
        )

        await _seed_day_and_activity(conn, TRAVELER_TRIP_UUID, activity_name, dia=1)

        inserted = await write_activity_participants(
            conn,
            TRAVELER_TRIP_UUID,
            [{
                "trip_uuid": TRAVELER_TRIP_UUID,
                "dia": 1,
                "atividade_nome": activity_name,
                "traveler_phone": phone,
                "status": "allowed",
            }],
        )

        assert inserted == 1
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_staff_task_import_is_scoped_to_trip_staff_for_that_trip(database_url):
    """A staff task must be assignable only to someone who is staff ON THIS TRIP
    (a trip_staff row for it) — not by global users.role. A person who is staff
    only on another trip must be rejected; a person staff on this trip succeeds.
    """
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        activity_name = "Coordenacao Chegada"
        await _seed_day_and_activity(conn, OTHER_TRIP_UUID, activity_name, dia=1)

        elsewhere_staff_phone = "+5511990002222"
        await write_staff(
            conn,
            STAFF_TRIP_UUID,
            [{
                "phone": elsewhere_staff_phone,
                "nome": "Staff Elsewhere",
                "funcao": "Suporte",
                "trip_uuid": STAFF_TRIP_UUID,
                "photo_url": None,
                "bio": None,
            }],
        )

        with pytest.raises(StaffTaskImportError, match="staff not found"):
            await write_staff_tasks(
                conn,
                OTHER_TRIP_UUID,
                [{
                    "dia": 1,
                    "atividade_nome": activity_name,
                    "staff_phone": elsewhere_staff_phone,
                    "titulo": "Receber grupo",
                    "descricao": None,
                    "sort_order": 1,
                }],
            )

        this_trip_staff_phone = "+5511990003333"
        await write_staff(
            conn,
            OTHER_TRIP_UUID,
            [{
                "phone": this_trip_staff_phone,
                "nome": "Staff Here",
                "funcao": "Suporte",
                "trip_uuid": OTHER_TRIP_UUID,
                "photo_url": None,
                "bio": None,
            }],
        )

        inserted = await write_staff_tasks(
            conn,
            OTHER_TRIP_UUID,
            [{
                "dia": 1,
                "atividade_nome": activity_name,
                "staff_phone": this_trip_staff_phone,
                "titulo": "Receber grupo",
                "descricao": None,
                "sort_order": 1,
            }],
        )

        assert inserted == 1
    finally:
        await conn.close()

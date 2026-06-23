"""Integration tests for GET /me/trip, /me/trip/phases and /me/trip/travelers."""

import asyncio
import uuid as _uuid
from datetime import date

from sqlalchemy import select

from app.db.models.trip import TripPhase, TripTraveler
from app.db.models.user import User
from app.services.qr_service import decode_traveler_qr_payload

TEST_TRIP_UUID = "trip-routes-test-001"


# ── Seed helpers ──────────────────────────────────────────────────────────────

async def _seed_trip(session_factory, *, user_phone: str, trip_uuid: str = TEST_TRIP_UUID):
    """Create user + synced trip_traveler assignment."""
    async with session_factory() as session:
        from sqlalchemy import text
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": trip_uuid,
                "title": "Test Trip",
                "dest": "Brazil",
                "sd": date(2026, 7, 1),
                "ed": date(2026, 7, 10),
            },
        )
        user = User(phone=user_phone, full_name="Trip Tester", status="active")
        session.add(user)
        await session.flush()
        tt = TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=user.id)
        session.add(tt)
        await session.commit()
        return str(user.id)


async def _seed_phases(session_factory, *, trip_uuid: str = TEST_TRIP_UUID):
    """Add pre-trip and in-trip phases to the trip."""
    async with session_factory() as session:
        pre = TripPhase(
            wetravel_trip_uuid=trip_uuid,
            phase_type="pre-trip",
            title="Visa",
            subtitle="Entry requirements",
            icon="passport",
            short_description="Check visa requirements.",
            detailed_description=None,
            sort_order=0,
            starts_at=None,
            is_locked_by_default=False,
            is_visible=True,
        )
        in_trip = TripPhase(
            wetravel_trip_uuid=trip_uuid,
            phase_type="in-trip",
            title="Day 1 — Arrival",
            subtitle="Arrival",
            icon="plane-landing",
            short_description="Airport transfer.",
            detailed_description=None,
            sort_order=1,
            starts_at=None,
            is_locked_by_default=False,
            is_visible=True,
        )
        session.add_all([pre, in_trip])
        await session.commit()


def _auth(seeded_client, phone: str) -> dict:
    """Return Authorization headers for the given phone."""
    otp_res = seeded_client.post("/auth/request-otp", json={"phone": phone})
    verify_res = seeded_client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_res.json()["debug_code"]},
    )
    data = verify_res.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_get_my_trip_phases_returns_phases_with_correct_shape(seeded_client, session_factory):
    """GET /me/trip/phases returns phases with checklist_items and links fields."""
    phone = "+5511333000003"
    asyncio.run(_seed_trip(session_factory, user_phone=phone))
    asyncio.run(_seed_phases(session_factory))
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/trip/phases", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "phases" in data
    assert len(data["phases"]) == 2
    phase_types = {p["phase_type"] for p in data["phases"]}
    assert phase_types == {"pre-trip", "in-trip"}
    for phase in data["phases"]:
        assert "id" in phase
        assert "title" in phase
        assert "sort_order" in phase
        assert "checklist_items" in phase
        assert "links" in phase
        assert isinstance(phase["checklist_items"], list)
        assert isinstance(phase["links"], list)


def test_get_my_qr_code_returns_signed_traveler_payload(seeded_client, session_factory):
    """GET /me/qr-code returns the authenticated traveler's signed QR payload."""
    phone = "+5511333000010"
    trip_uuid = "trip-qr-code-test-001"
    user_id = asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))

    async def _get_trip_traveler_id():
        async with session_factory() as session:
            trip_traveler = await session.scalar(
                select(TripTraveler).where(
                    TripTraveler.user_id == _uuid.UUID(user_id),
                    TripTraveler.wetravel_trip_uuid == trip_uuid,
                )
            )
            return str(trip_traveler.id)

    trip_traveler_id = asyncio.run(_get_trip_traveler_id())
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/qr-code", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["trip_uuid"] == trip_uuid
    assert data["trip_traveler_id"] == trip_traveler_id
    assert "qr_payload" in data
    decoded_payload = decode_traveler_qr_payload(data["qr_payload"])
    assert decoded_payload["trip_uuid"] == trip_uuid
    assert decoded_payload["trip_traveler_id"] == trip_traveler_id


def test_get_my_qr_code_returns_404_without_synced_trip(seeded_client, session_factory):
    """GET /me/qr-code does not mint QR payloads for unsynced trip assignments."""
    phone = "+5511333000011"
    orphan_trip_uuid = "trip-qr-code-unsynced-001"

    async def _seed_unsynced_trip_assignment():
        async with session_factory() as session:
            user = User(phone=phone, full_name="Unsynced Trip", status="active")
            session.add(user)
            await session.flush()
            session.add(
                TripTraveler(
                    wetravel_trip_uuid=orphan_trip_uuid,
                    user_id=user.id,
                )
            )
            await session.commit()

    asyncio.run(_seed_unsynced_trip_assignment())
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/qr-code", headers=headers)

    assert response.status_code == 404


def test_get_my_trip_phases_returns_404_when_no_trip_assigned(seeded_client, session_factory):
    """GET /me/trip/phases returns 404 when user has no trip assignment."""
    phone = "+5511333000004"
    # Create user but NO trip_traveler row
    async def _seed_user_only():
        async with session_factory() as session:
            user = User(phone=phone, full_name="No Trip", status="active")
            session.add(user)
            await session.commit()
    asyncio.run(_seed_user_only())
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/trip/phases", headers=headers)

    assert response.status_code == 404


def test_get_my_trip_travelers_returns_all_trip_members(seeded_client, session_factory):
    """GET /me/trip/travelers returns all travelers in the same trip."""
    phone_a = "+5511333000005"
    phone_b = "+5511333000006"
    trip_uuid = "trip-travelers-test-001"

    asyncio.run(_seed_trip(session_factory, user_phone=phone_a, trip_uuid=trip_uuid))

    async def _seed_second_traveler():
        async with session_factory() as session:
            user_b = User(phone=phone_b, full_name="Traveler B", status="active")
            session.add(user_b)
            await session.flush()
            session.add(TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=user_b.id))
            await session.commit()
    asyncio.run(_seed_second_traveler())

    headers = _auth(seeded_client, phone_a)
    response = seeded_client.get("/me/trip/travelers", headers=headers)

    assert response.status_code == 200
    travelers = response.json()["travelers"]
    phones = {t["phone"] for t in travelers}
    assert phone_a in phones
    assert phone_b in phones


def test_get_my_trip_travelers_includes_current_phase_id(seeded_client, session_factory):
    """Each traveler in the response has a current_phase_id field."""
    phone = "+5511333000007"
    trip_uuid = "trip-phase-id-test-001"

    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))

    async def _seed_phase():
        async with session_factory() as session:
            phase = TripPhase(
                wetravel_trip_uuid=trip_uuid,
                phase_type="pre-trip",
                title="Visa",
                subtitle=None,
                icon=None,
                short_description="Check requirements.",
                detailed_description=None,
                sort_order=0,
                starts_at=None,
                is_locked_by_default=False,
                is_visible=True,
            )
            session.add(phase)
            await session.commit()
    asyncio.run(_seed_phase())

    headers = _auth(seeded_client, phone)
    response = seeded_client.get("/me/trip/travelers", headers=headers)

    assert response.status_code == 200
    travelers = response.json()["travelers"]
    assert len(travelers) >= 1
    for traveler in travelers:
        assert "current_phase_id" in traveler
        assert traveler["current_phase_id"] is not None

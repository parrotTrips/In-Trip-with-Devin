"""Integration tests for GET /me/trip, /me/trip/phases and /me/trip/travelers."""

import asyncio
import uuid as _uuid
from datetime import date
from unittest.mock import patch

from sqlalchemy import func, select

from app.db.models.staff import TripAnnouncement, TripAnnouncementRead
from app.db.models.trip import TravelerAppFeedback, TripPhase, TripRecommendation, TripTraveler
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
                "sd": date(2027, 7, 1),
                "ed": date(2027, 7, 10),
            },
        )
        user = User(phone=user_phone, full_name="Trip Tester", status="active")
        session.add(user)
        await session.flush()
        tt = TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=user.id)
        session.add(tt)
        await session.commit()
        return str(user.id)


async def _set_service_agreement_url(session_factory, *, trip_uuid: str, service_agreement_url: str):
    async with session_factory() as session:
        from sqlalchemy import text
        await session.execute(
            text(
                "UPDATE wetravel_trips SET service_agreement_url = :url WHERE trip_uuid = :trip_uuid"
            ),
            {"url": service_agreement_url, "trip_uuid": trip_uuid},
        )
        await session.commit()


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


async def _seed_announcements(session_factory, *, trip_uuid: str, count: int = 2, is_anonymous: bool = False):
    async with session_factory() as session:
        sender = User(phone=f"+5511777{trip_uuid[-6:]}", full_name="Staff Sender", status="active", role="staff")
        session.add(sender)
        await session.flush()

        announcements = [
            TripAnnouncement(
                wetravel_trip_uuid=trip_uuid,
                title=f"Update {index}",
                body=f"Message body {index}",
                sent_by_user_id=sender.id,
                is_anonymous=is_anonymous,
            )
            for index in range(1, count + 1)
        ]
        session.add_all(announcements)
        await session.commit()
        return [str(announcement.id) for announcement in announcements]


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

def test_trip_announcement_read_model_is_registered():
    """Announcement read receipts are available through the model registry."""
    from app.db.models import TripAnnouncementRead

    assert TripAnnouncementRead.__tablename__ == "trip_announcement_reads"


def test_get_my_announcements_returns_read_state_and_unread_count(seeded_client, session_factory):
    phone = "+5511333000013"
    trip_uuid = "trip-announcement-read-list"
    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))
    asyncio.run(_seed_announcements(session_factory, trip_uuid=trip_uuid, count=2))
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/announcements", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["unread_count"] == 2
    assert len(data["announcements"]) == 2
    assert {announcement["is_read"] for announcement in data["announcements"]} == {False}


def test_get_my_announcements_labels_anonymous_sender_as_parrot_team(seeded_client, session_factory):
    phone = "+5511333000019"
    trip_uuid = "trip-announcement-anonymous"
    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))
    asyncio.run(_seed_announcements(session_factory, trip_uuid=trip_uuid, count=1, is_anonymous=True))
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/announcements", headers=headers)

    assert response.status_code == 200
    assert response.json()["announcements"][0]["sent_by"] == "Parrot Team"


def test_mark_announcement_read_updates_only_that_announcement(seeded_client, session_factory):
    phone = "+5511333000014"
    trip_uuid = "trip-announcement-read-one"
    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))
    announcement_ids = asyncio.run(_seed_announcements(session_factory, trip_uuid=trip_uuid, count=2))
    headers = _auth(seeded_client, phone)

    response = seeded_client.post(f"/me/announcements/{announcement_ids[0]}/read", headers=headers)

    assert response.status_code == 200
    assert response.json()["announcement_id"] == announcement_ids[0]

    list_response = seeded_client.get("/me/announcements", headers=headers)
    data = list_response.json()
    read_by_id = {announcement["id"]: announcement["is_read"] for announcement in data["announcements"]}
    assert data["unread_count"] == 1
    assert read_by_id[announcement_ids[0]] is True
    assert read_by_id[announcement_ids[1]] is False


def test_mark_announcement_read_is_idempotent(seeded_client, session_factory):
    phone = "+5511333000015"
    trip_uuid = "trip-announcement-read-idem"
    user_id = asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))
    announcement_id = asyncio.run(_seed_announcements(session_factory, trip_uuid=trip_uuid, count=1))[0]
    headers = _auth(seeded_client, phone)

    for _ in range(2):
        response = seeded_client.post(f"/me/announcements/{announcement_id}/read", headers=headers)
        assert response.status_code == 200

    async def _count_reads():
        async with session_factory() as session:
            return await session.scalar(
                select(func.count())
                .select_from(TripAnnouncementRead)
                .where(
                    TripAnnouncementRead.announcement_id == _uuid.UUID(announcement_id),
                    TripAnnouncementRead.user_id == _uuid.UUID(user_id),
                )
            )

    assert asyncio.run(_count_reads()) == 1


def test_mark_announcement_read_rejects_other_trip(seeded_client, session_factory):
    phone = "+5511333000016"
    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid="trip-announcement-read-home"))
    other_announcement_id = asyncio.run(
        _seed_announcements(session_factory, trip_uuid="trip-announcement-read-away", count=1)
    )[0]
    headers = _auth(seeded_client, phone)

    response = seeded_client.post(f"/me/announcements/{other_announcement_id}/read", headers=headers)

    assert response.status_code == 404


def test_get_my_app_feedback_returns_empty_feedback(seeded_client, session_factory):
    phone = "+5511333000017"
    trip_uuid = "trip-app-feedback-empty"
    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/app-feedback", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"feedback": None}


def test_put_my_app_feedback_upserts_one_feedback_per_traveler(seeded_client, session_factory):
    phone = "+5511333000018"
    trip_uuid = "trip-app-feedback-upsert"
    user_id = asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))
    headers = _auth(seeded_client, phone)

    create_response = seeded_client.put("/me/app-feedback", headers=headers, json={"feedback": "The app helped a lot."})
    update_response = seeded_client.put("/me/app-feedback", headers=headers, json={"feedback": "Updated feedback."})

    assert create_response.status_code == 200
    assert create_response.json()["feedback"] == "The app helped a lot."
    assert update_response.status_code == 200
    assert update_response.json()["feedback"] == "Updated feedback."

    async def _stored_feedback():
        async with session_factory() as session:
            trip_traveler = await session.scalar(
                select(TripTraveler).where(
                    TripTraveler.user_id == _uuid.UUID(user_id),
                    TripTraveler.wetravel_trip_uuid == trip_uuid,
                )
            )
            rows = (await session.execute(
                select(TravelerAppFeedback).where(TravelerAppFeedback.trip_traveler_id == trip_traveler.id)
            )).scalars().all()
            return rows

    rows = asyncio.run(_stored_feedback())
    assert len(rows) == 1
    assert rows[0].feedback == "Updated feedback."

    get_response = seeded_client.get("/me/app-feedback", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["feedback"] == "Updated feedback."


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


def test_health_alias_is_public(seeded_client):
    """GET /health is usable by Cloud Run and external monitors without JWT."""
    response = seeded_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_my_trip_returns_signed_service_agreement_url_for_gcs_uri(seeded_client, session_factory):
    """GET /me/trip resolves private GCS service agreements into signed URLs."""
    phone = "+5511333000012"
    trip_uuid = "trip-service-agreement-gcs-001"
    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))
    asyncio.run(_set_service_agreement_url(
        session_factory,
        trip_uuid=trip_uuid,
        service_agreement_url="gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf",
    ))
    headers = _auth(seeded_client, phone)

    with patch(
        "app.routers.trip.resolve_service_agreement_url",
        return_value="https://storage.googleapis.com/signed-service-agreement",
    ) as resolver:
        response = seeded_client.get("/me/trip", headers=headers)

    assert response.status_code == 200
    trip = response.json()["trip"]
    assert trip["service_agreement_url"] == "https://storage.googleapis.com/signed-service-agreement"
    resolver.assert_called_once_with(
        "gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf"
    )


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


def test_get_my_recommendations_returns_rich_filter_fields(seeded_client, session_factory):
    """GET /me/recommendations exposes the sheet-backed fields needed by the rich UI."""
    phone = "+5511333000013"
    trip_uuid = "trip-rich-recommendations-001"
    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))

    async def _seed_recommendation():
        async with session_factory() as session:
            session.add(
                TripRecommendation(
                    wetravel_trip_uuid=trip_uuid,
                    name="Babbo Osteria",
                    description="Upscale Italian cuisine",
                    address="Rua Barao da Torre, Ipanema",
                    photo_url="https://example.com/babbo.jpg",
                    sort_order=1,
                    category="restaurants",
                    neighborhood="Ipanema",
                    location="rio",
                    highlight="Near the hotel",
                    price_range="$$$",
                    rating=4.7,
                    map_url="https://maps.example/babbo",
                    emoji="🍝",
                )
            )
            await session.commit()

    asyncio.run(_seed_recommendation())
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/recommendations", headers=headers)

    assert response.status_code == 200
    rec = response.json()["recommendations"][0]
    assert rec["category"] == "restaurants"
    assert rec["neighborhood"] == "Ipanema"
    assert rec["location"] == "rio"
    assert rec["highlight"] == "Near the hotel"
    assert rec["price_range"] == "$$$"
    assert rec["rating"] == 4.7
    assert rec["map_url"] == "https://maps.example/babbo"
    assert rec["emoji"] == "🍝"

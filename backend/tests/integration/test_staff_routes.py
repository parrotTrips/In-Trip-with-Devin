import asyncio
from datetime import date

from sqlalchemy import func, select, text

from app.db.models.staff import ActivityCheckin, StaffTask
from app.db.models.trip import TripActivity, TripPhase, TripTraveler
from app.db.models.user import User
from app.services.qr_service import create_traveler_qr_payload


async def _seed_staff_trip_with_tasks(session_factory, *, seed_checkin: bool = False):
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": "staff-route-test",
                "title": "Staff Route Test",
                "dest": "Brazil",
                "sd": date(2026, 7, 1),
                "ed": date(2026, 7, 10),
            },
        )
        staff = User(phone="+5511888000001", full_name="Staff One", status="active", role="staff")
        other_staff = User(phone="+5511888000002", full_name="Staff Two", status="active", role="staff")
        traveler = User(
            phone="+5511888000003",
            full_name="Traveler One",
            status="active",
            role="traveler",
        )
        second_traveler = User(
            phone="+5511888000005",
            full_name="Traveler Two",
            status="active",
            role="traveler",
        )
        other_trip_traveler_user = User(
            phone="+5511888000004",
            full_name="Other Trip Traveler",
            status="active",
        )
        session.add_all([staff, other_staff, traveler, second_traveler, other_trip_traveler_user])
        await session.flush()
        staff_trip_traveler = TripTraveler(wetravel_trip_uuid="staff-route-test", user_id=staff.id)
        session.add(staff_trip_traveler)
        session.add(TripTraveler(wetravel_trip_uuid="staff-route-test", user_id=other_staff.id))
        trip_traveler = TripTraveler(wetravel_trip_uuid="staff-route-test", user_id=traveler.id)
        session.add(trip_traveler)
        second_trip_traveler = TripTraveler(
            wetravel_trip_uuid="staff-route-test",
            user_id=second_traveler.id,
        )
        session.add(second_trip_traveler)
        await session.flush()

        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": "staff-route-other-trip-test",
                "title": "Other Staff Route Test",
                "dest": "Argentina",
                "sd": date(2026, 7, 1),
                "ed": date(2026, 7, 10),
            },
        )
        other_trip_traveler = TripTraveler(
            wetravel_trip_uuid="staff-route-other-trip-test",
            user_id=other_trip_traveler_user.id,
        )
        session.add(other_trip_traveler)

        phase = TripPhase(
            wetravel_trip_uuid="staff-route-test",
            phase_type="in-trip",
            title="Day 1 — Arrival",
            subtitle="Arrival",
            icon="plane-landing",
            short_description="Arrival day",
            detailed_description=None,
            sort_order=0,
            starts_at=None,
            is_locked_by_default=False,
            is_visible=True,
        )
        session.add(phase)
        await session.flush()

        activity = TripActivity(
            trip_phase_id=phase.id,
            name="Airport Transfer",
            activity_type="logistics",
            starts_at=None,
            duration_minutes=None,
            short_description="Airport pickup",
            practical_info=None,
            amount_brl=None,
            sort_order=0,
        )
        session.add(activity)
        second_activity = TripActivity(
            trip_phase_id=phase.id,
            name="Welcome Briefing",
            activity_type="meeting",
            starts_at=None,
            duration_minutes=None,
            short_description="Trip orientation",
            practical_info=None,
            amount_brl=None,
            sort_order=1,
        )
        session.add(second_activity)
        await session.flush()

        session.add_all([
            StaffTask(
                trip_phase_id=phase.id,
                trip_activity_id=activity.id,
                assigned_to_user_id=staff.id,
                title="Coordenar van 1",
                description="Receber viajantes no aeroporto",
                starts_at=None,
                sort_order=1,
            ),
            StaffTask(
                trip_phase_id=phase.id,
                trip_activity_id=activity.id,
                assigned_to_user_id=other_staff.id,
                title="Tarefa invisível",
                description="Nao deve aparecer para Staff One",
                starts_at=None,
                sort_order=1,
            ),
        ])
        if seed_checkin:
            session.add(
                ActivityCheckin(
                    trip_activity_id=activity.id,
                    trip_traveler_id=trip_traveler.id,
                    scanned_by_user_id=staff.id,
                )
            )
        await session.commit()
        return {
            "staff_user_id": str(staff.id),
            "other_staff_user_id": str(other_staff.id),
            "activity_id": str(activity.id),
            "second_activity_id": str(second_activity.id),
            "trip_traveler_id": str(trip_traveler.id),
            "second_trip_traveler_id": str(second_trip_traveler.id),
            "staff_trip_traveler_id": str(staff_trip_traveler.id),
            "qr_payload": create_traveler_qr_payload(
                trip_traveler_id=str(trip_traveler.id),
                trip_uuid="staff-route-test",
            ),
            "staff_qr_payload": create_traveler_qr_payload(
                trip_traveler_id=str(staff_trip_traveler.id),
                trip_uuid="staff-route-test",
            ),
            "other_trip_qr_payload": create_traveler_qr_payload(
                trip_traveler_id=str(other_trip_traveler.id),
                trip_uuid="staff-route-other-trip-test",
            ),
        }


def _auth(client, phone: str) -> dict:
    otp_res = client.post("/auth/request-otp", json={"phone": phone})
    verify_res = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_res.json()["debug_code"]},
    )
    return {"Authorization": f"Bearer {verify_res.json()['access_token']}"}


def test_get_staff_trip_includes_only_current_staff_tasks(seeded_client, session_factory):
    asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.get("/me/staff/trip", headers=headers)

    assert response.status_code == 200
    activity = response.json()["days"][0]["activities"][0]
    assert activity["staff_tasks"] == [
        {
            "id": activity["staff_tasks"][0]["id"],
            "title": "Coordenar van 1",
            "description": "Receber viajantes no aeroporto",
            "sort_order": 1,
        }
    ]


def test_get_staff_trip_activity_includes_per_activity_checkin_counters(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory, seed_checkin=True))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.get("/me/staff/trip", headers=headers)

    assert response.status_code == 200
    activities = response.json()["days"][0]["activities"]
    activity_by_id = {activity["id"]: activity for activity in activities}
    assert activity_by_id[seed["activity_id"]]["checkin_count"] == 1
    assert activity_by_id[seed["activity_id"]]["traveler_count"] == 2
    assert activity_by_id[seed["second_activity_id"]]["checkin_count"] == 0
    assert activity_by_id[seed["second_activity_id"]]["traveler_count"] == 2


def test_scan_activity_checkin_returns_checked_in(seeded_client, session_factory):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=headers,
        json={"qr_payload": seed["qr_payload"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "checked_in"
    assert data["trip_activity_id"] == seed["activity_id"]
    assert data["trip_traveler_id"] == seed["trip_traveler_id"]
    assert data["scanned_by_user_id"] == seed["staff_user_id"]
    assert data["checkin_id"]
    assert data["checked_in_at"]


def test_scan_activity_checkin_duplicate_returns_existing_checkin(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    staff_one_headers = _auth(seeded_client, "+5511888000001")
    staff_two_headers = _auth(seeded_client, "+5511888000002")

    first_response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=staff_one_headers,
        json={"qr_payload": seed["qr_payload"]},
    )
    duplicate_response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=staff_two_headers,
        json={"qr_payload": seed["qr_payload"]},
    )

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 200
    duplicate = duplicate_response.json()
    assert duplicate["status"] == "already_checked_in"
    assert duplicate["checkin_id"] == first_response.json()["checkin_id"]
    assert duplicate["trip_activity_id"] == seed["activity_id"]
    assert duplicate["trip_traveler_id"] == seed["trip_traveler_id"]
    assert duplicate["scanned_by_user_id"] == seed["staff_user_id"]
    assert duplicate["scanned_by_user_id"] != seed["other_staff_user_id"]
    assert duplicate["scanned_by_name"] == "Staff One"


def test_scan_activity_checkin_duplicate_does_not_insert_second_row(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    for _ in range(2):
        response = seeded_client.post(
            f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
            headers=headers,
            json={"qr_payload": seed["qr_payload"]},
        )
        assert response.status_code == 200

    async def _count_checkins():
        async with session_factory() as session:
            return await session.scalar(
                select(func.count())
                .select_from(ActivityCheckin)
                .where(
                    ActivityCheckin.trip_activity_id == seed["activity_id"],
                    ActivityCheckin.trip_traveler_id == seed["trip_traveler_id"],
                )
            )

    assert asyncio.run(_count_checkins()) == 1


def test_scan_activity_checkin_rejects_wrong_trip_qr(seeded_client, session_factory):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=headers,
        json={"qr_payload": seed["other_trip_qr_payload"]},
    )

    assert response.status_code in (400, 403)

    async def _count_checkins():
        async with session_factory() as session:
            return await session.scalar(
                select(func.count())
                .select_from(ActivityCheckin)
                .where(ActivityCheckin.trip_activity_id == seed["activity_id"])
            )

    assert asyncio.run(_count_checkins()) == 0


def test_scan_activity_checkin_rejects_non_traveler_qr(seeded_client, session_factory):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=headers,
        json={"qr_payload": seed["staff_qr_payload"]},
    )

    assert response.status_code in (400, 403)

    async def _count_checkins():
        async with session_factory() as session:
            return await session.scalar(
                select(func.count())
                .select_from(ActivityCheckin)
                .where(
                    ActivityCheckin.trip_activity_id == seed["activity_id"],
                    ActivityCheckin.trip_traveler_id == seed["staff_trip_traveler_id"],
                )
            )

    assert asyncio.run(_count_checkins()) == 0


def test_scan_activity_checkin_uses_authenticated_staff_user(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=headers,
        json={"qr_payload": seed["qr_payload"]},
    )

    assert response.status_code == 200
    assert response.json()["scanned_by_user_id"] == seed["staff_user_id"]


def test_scan_activity_checkin_rejects_same_trip_non_staff_user(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    traveler_headers = _auth(seeded_client, "+5511888000003")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=traveler_headers,
        json={"qr_payload": seed["qr_payload"]},
    )

    assert response.status_code == 403

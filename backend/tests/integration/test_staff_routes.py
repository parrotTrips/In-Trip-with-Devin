import asyncio
from datetime import date

from sqlalchemy import delete, func, select, text

from app.db.models.staff import (
    ActivityCheckin,
    ActivityCheckinScanEvent,
    ActivityParticipant,
    StaffTask,
    TripAnnouncement,
    TripStaff,
)
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
                "sd": date(2027, 7, 1),
                "ed": date(2027, 7, 10),
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
        session.add_all(
            [
                TripStaff(wetravel_trip_uuid="staff-route-test", user_id=staff.id),
                TripStaff(wetravel_trip_uuid="staff-route-test", user_id=other_staff.id),
            ]
        )
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
                "sd": date(2027, 7, 1),
                "ed": date(2027, 7, 10),
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
            "other_trip_traveler_id": str(other_trip_traveler.id),
            "staff_trip_traveler_id": str(staff_trip_traveler.id),
            "qr_payload": create_traveler_qr_payload(
                trip_traveler_id=str(trip_traveler.id),
                trip_uuid="staff-route-test",
            ),
            "second_qr_payload": create_traveler_qr_payload(
                trip_traveler_id=str(second_trip_traveler.id),
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


async def _seed_cross_trip_activity(session_factory, seed):
    async with session_factory() as session:
        other_phase = TripPhase(
            wetravel_trip_uuid="staff-route-other-trip-test",
            phase_type="in-trip",
            title="Other Trip Day",
            short_description="Other trip day",
            sort_order=0,
            is_locked_by_default=False,
            is_visible=True,
        )
        session.add(other_phase)
        await session.flush()
        other_activity = TripActivity(
            trip_phase_id=other_phase.id,
            name="Other Trip Activity",
            activity_type="meeting",
            short_description="Other trip activity",
            sort_order=0,
        )
        session.add(other_activity)
        await session.commit()
        return str(other_activity.id)


async def _seed_inconsistent_controlled_participant(session_factory, seed):
    async with session_factory() as session:
        session.add_all(
            [
                ActivityParticipant(
                    trip_activity_id=seed["activity_id"],
                    trip_traveler_id=seed["trip_traveler_id"],
                    status="allowed",
                ),
                ActivityParticipant(
                    trip_activity_id=seed["activity_id"],
                    trip_traveler_id=seed["other_trip_traveler_id"],
                    status="allowed",
                ),
            ]
        )
        await session.commit()


async def _seed_controlled_participants_with_per_trip_roles(session_factory, seed):
    async with session_factory() as session:
        cross_role_user = User(
            phone="+5511888000788",
            full_name="Staff Only Elsewhere",
            status="active",
            role="staff",
        )
        session.add(cross_role_user)
        await session.flush()
        cross_role_traveler = TripTraveler(
            wetravel_trip_uuid="staff-route-test",
            user_id=cross_role_user.id,
        )
        session.add(cross_role_traveler)
        session.add(
            TripStaff(
                wetravel_trip_uuid="staff-route-other-trip-test",
                user_id=cross_role_user.id,
            )
        )
        await session.flush()
        session.add_all(
            [
                ActivityParticipant(
                    trip_activity_id=seed["activity_id"],
                    trip_traveler_id=seed["trip_traveler_id"],
                    status="allowed",
                ),
                ActivityParticipant(
                    trip_activity_id=seed["activity_id"],
                    trip_traveler_id=seed["staff_trip_traveler_id"],
                    status="allowed",
                ),
                ActivityParticipant(
                    trip_activity_id=seed["activity_id"],
                    trip_traveler_id=cross_role_traveler.id,
                    status="allowed",
                ),
            ]
        )
        await session.commit()
        return str(cross_role_traveler.id)


async def _seed_other_trip_announcement(session_factory, seed):
    async with session_factory() as session:
        announcement = TripAnnouncement(
            wetravel_trip_uuid="staff-route-other-trip-test",
            title="Other trip announcement",
            body="Must remain isolated",
            sent_by_user_id=seed["staff_user_id"],
        )
        session.add(announcement)
        await session.commit()
        return str(announcement.id)


async def _seed_inconsistent_cross_trip_checkin(session_factory, seed):
    async with session_factory() as session:
        session.add(
            ActivityCheckin(
                trip_activity_id=seed["activity_id"],
                trip_traveler_id=seed["other_trip_traveler_id"],
                scanned_by_user_id=seed["staff_user_id"],
            )
        )
        await session.commit()


def _auth(client, phone: str) -> dict:
    otp_res = client.post("/auth/request-otp", json={"phone": phone})
    verify_res = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_res.json()["debug_code"]},
    )
    return {"Authorization": f"Bearer {verify_res.json()['access_token']}"}


async def _seed_mixed_role_staff(session_factory):
    async with session_factory() as session:
        for trip_id, title in [
            ("mixed-staff-trip", "Mixed Staff Trip"),
            ("mixed-traveler-trip", "Mixed Traveler Trip"),
        ]:
            await session.execute(
                text(
                    "INSERT INTO wetravel_trips "
                    "(trip_uuid, title, destination, start_date, end_date) "
                    "VALUES (:trip_id, :title, 'Brazil', '2027-08-01', '2027-08-10')"
                ),
                {"trip_id": trip_id, "title": title},
            )

        user = User(
            phone="+5511888000099",
            full_name="Mixed Role Person",
            status="active",
            role="traveler",
        )
        session.add(user)
        await session.flush()
        session.add_all(
            [
                TripTraveler(wetravel_trip_uuid="mixed-staff-trip", user_id=user.id),
                TripTraveler(wetravel_trip_uuid="mixed-traveler-trip", user_id=user.id),
                TripStaff(wetravel_trip_uuid="mixed-staff-trip", user_id=user.id),
            ]
        )
        await session.commit()
        return str(user.id)


def _scoped_auth(user_id: str, phone: str, trip_id: str, role: str) -> dict:
    from app.services.auth_service import _create_session_token

    token = _create_session_token(user_id, phone, trip_id, role)
    return {"Authorization": f"Bearer {token}"}


def test_staff_access_is_authorized_per_selected_trip(seeded_client, session_factory):
    user_id = asyncio.run(_seed_mixed_role_staff(session_factory))

    staff_response = seeded_client.get(
        "/me/staff/trip/contacts",
        headers=_scoped_auth(user_id, "+5511888000099", "mixed-staff-trip", "staff"),
    )
    traveler_response = seeded_client.get(
        "/me/staff/trip/contacts",
        headers=_scoped_auth(
            user_id,
            "+5511888000099",
            "mixed-traveler-trip",
            "traveler",
        ),
    )

    assert staff_response.status_code == 200
    assert staff_response.json()["wetravel_trip_uuid"] == "mixed-staff-trip"
    assert traveler_response.status_code == 403


def test_staff_access_uses_database_membership_when_token_role_is_traveler(
    seeded_client,
    session_factory,
):
    user_id = asyncio.run(_seed_mixed_role_staff(session_factory))

    response = seeded_client.get(
        "/me/staff/trip/contacts",
        headers=_scoped_auth(
            user_id,
            "+5511888000099",
            "mixed-staff-trip",
            "traveler",
        ),
    )

    assert response.status_code == 200
    assert response.json()["wetravel_trip_uuid"] == "mixed-staff-trip"


def test_staff_access_revalidates_membership_after_token_issuance(
    seeded_client,
    session_factory,
):
    user_id = asyncio.run(_seed_mixed_role_staff(session_factory))
    headers = _scoped_auth(user_id, "+5511888000099", "mixed-staff-trip", "staff")

    async def _remove_staff_membership():
        async with session_factory() as session:
            await session.execute(
                delete(TripStaff).where(
                    TripStaff.user_id == user_id,
                    TripStaff.wetravel_trip_uuid == "mixed-staff-trip",
                )
            )
            await session.commit()

    asyncio.run(_remove_staff_membership())
    response = seeded_client.get("/me/staff/trip/contacts", headers=headers)

    assert response.status_code == 403


def test_activity_travelers_excludes_controlled_participant_from_other_trip(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    asyncio.run(_seed_inconsistent_controlled_participant(session_factory, seed))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.get(
        f"/me/staff/activities/{seed['activity_id']}/travelers",
        headers=headers,
    )

    assert response.status_code == 200
    assert [row["id"] for row in response.json()["travelers"]] == [
        seed["trip_traveler_id"]
    ]


def test_open_activity_travelers_excludes_staff_on_this_trip(
    seeded_client,
    session_factory,
):
    """`/activities/{id}/travelers` on an open (uncontrolled) activity must not
    list people who are `trip_staff` on this trip, even though they hold a
    `trip_travelers` row too (so they can use the traveler view).
    """
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.get(
        f"/me/staff/activities/{seed['second_activity_id']}/travelers",
        headers=headers,
    )

    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["travelers"]}
    assert seed["staff_trip_traveler_id"] not in ids
    assert seed["trip_traveler_id"] in ids
    assert seed["second_trip_traveler_id"] in ids


def test_staff_trip_summary_excludes_controlled_participant_from_other_trip(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    asyncio.run(_seed_inconsistent_controlled_participant(session_factory, seed))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.get("/me/staff/trip", headers=headers)

    assert response.status_code == 200
    activity = next(
        activity
        for activity in response.json()["days"][0]["activities"]
        if activity["id"] == seed["activity_id"]
    )
    assert activity["traveler_count"] == 1
    assert activity["absent_travelers"] == ["Traveler One"]


def test_controlled_activity_excludes_same_trip_staff_but_keeps_staff_from_other_trip(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    cross_role_traveler_id = asyncio.run(
        _seed_controlled_participants_with_per_trip_roles(session_factory, seed)
    )
    headers = _auth(seeded_client, "+5511888000001")

    summary = seeded_client.get("/me/staff/trip", headers=headers)
    eligible = seeded_client.get(
        f"/me/staff/activities/{seed['activity_id']}/travelers",
        headers=headers,
    )

    assert summary.status_code == 200
    activity = next(
        row
        for row in summary.json()["days"][0]["activities"]
        if row["id"] == seed["activity_id"]
    )
    assert activity["traveler_count"] == 2
    assert activity["absent_travelers"] == ["Staff Only Elsewhere", "Traveler One"]

    assert eligible.status_code == 200
    eligible_ids = {row["id"] for row in eligible.json()["travelers"]}
    assert eligible_ids == {seed["trip_traveler_id"], cross_role_traveler_id}
    assert seed["staff_trip_traveler_id"] not in eligible_ids


def test_staff_trip_summary_excludes_checkin_traveler_from_other_trip(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    asyncio.run(_seed_inconsistent_cross_trip_checkin(session_factory, seed))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.get("/me/staff/trip", headers=headers)

    assert response.status_code == 200
    activity = next(
        activity
        for activity in response.json()["days"][0]["activities"]
        if activity["id"] == seed["activity_id"]
    )
    assert activity["checkin_steps"] == []


def test_staff_activity_endpoints_reject_activity_from_other_trip(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    other_activity_id = asyncio.run(_seed_cross_trip_activity(session_factory, seed))
    headers = _auth(seeded_client, "+5511888000001")

    travelers = seeded_client.get(
        f"/me/staff/activities/{other_activity_id}/travelers",
        headers=headers,
    )
    preview = seeded_client.post(
        f"/me/staff/activities/{other_activity_id}/checkins/preview",
        headers=headers,
        json={"qr_payload": seed["other_trip_qr_payload"]},
    )
    scan = seeded_client.post(
        f"/me/staff/activities/{other_activity_id}/checkins/scan",
        headers=headers,
        json={"qr_payload": seed["other_trip_qr_payload"]},
    )

    assert travelers.status_code == 403
    assert preview.status_code == 403
    assert scan.status_code == 403


def test_staff_announcements_are_isolated_to_selected_trip(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    other_announcement_id = asyncio.run(
        _seed_other_trip_announcement(session_factory, seed)
    )
    headers = _auth(seeded_client, "+5511888000001")

    created = seeded_client.post(
        "/me/staff/announcements",
        headers=headers,
        json={"title": "Selected trip", "body": "Visible here"},
    )
    listed = seeded_client.get("/me/staff/announcements", headers=headers)
    updated = seeded_client.put(
        f"/me/staff/announcements/{other_announcement_id}",
        headers=headers,
        json={"title": "Leaked", "body": "Must be blocked"},
    )
    deleted = seeded_client.delete(
        f"/me/staff/announcements/{other_announcement_id}",
        headers=headers,
    )

    assert created.status_code == 200
    assert [row["title"] for row in listed.json()["announcements"]] == [
        "Selected trip"
    ]
    assert updated.status_code == 404
    assert deleted.status_code == 404


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
    # "Staff One" and "Staff Two" both hold a `trip_travelers` row on this trip (so
    # they can use the traveler view) AND a `trip_staff` row for this same trip —
    # that trip_staff row is what makes them staff here, and it must exclude them
    # from traveler counts and lists, per trip.
    assert activity_by_id[seed["activity_id"]]["checkin_steps"][0]["count"] == 1
    assert activity_by_id[seed["activity_id"]]["traveler_count"] == 2
    assert activity_by_id[seed["second_activity_id"]]["checkin_steps"] == []
    assert activity_by_id[seed["second_activity_id"]]["traveler_count"] == 2
    assert activity_by_id[seed["second_activity_id"]]["absent_travelers"] == [
        "Traveler One",
        "Traveler Two",
    ]


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


def test_preview_activity_checkin_identifies_traveler_without_checking_in(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/preview",
        headers=headers,
        json={"qr_payload": seed["qr_payload"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready_to_check_in"
    assert data["trip_activity_id"] == seed["activity_id"]
    assert data["trip_traveler_id"] == seed["trip_traveler_id"]
    assert data["traveler_name"] == "Traveler One"
    assert data["scan_number"] == 1
    assert data["max_checkins"] == 1

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

    assert asyncio.run(_count_checkins()) == 0


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


def test_scan_activity_checkin_rejects_staff_trip_membership_as_traveler(
    seeded_client,
    session_factory,
):
    """A `trip_travelers` row that belongs to someone who is also `trip_staff` on
    THIS trip must not be scannable as a traveler check-in — they are staff here,
    a `trip_travelers` row only exists so they can use the traveler view.
    """
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


def test_scan_activity_checkin_accepts_traveler_who_is_staff_on_another_trip(
    seeded_client,
    session_factory,
):
    """Staff-ness is derived per trip: someone who is `trip_staff` on a
    different trip but only a plain traveler here must still be scannable.
    """
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))

    async def _seed_cross_trip_staff_traveler():
        async with session_factory() as session:
            user = User(
                phone="+5511888000777",
                full_name="Staff Elsewhere",
                status="active",
            )
            session.add(user)
            await session.flush()
            trip_traveler = TripTraveler(
                wetravel_trip_uuid="staff-route-test", user_id=user.id
            )
            session.add(trip_traveler)
            session.add(
                TripStaff(
                    wetravel_trip_uuid="staff-route-other-trip-test", user_id=user.id
                )
            )
            await session.flush()
            qr_payload = create_traveler_qr_payload(
                trip_traveler_id=str(trip_traveler.id),
                trip_uuid="staff-route-test",
            )
            await session.commit()
            return {"trip_traveler_id": str(trip_traveler.id), "qr_payload": qr_payload}

    cross_trip_seed = asyncio.run(_seed_cross_trip_staff_traveler())
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=headers,
        json={"qr_payload": cross_trip_seed["qr_payload"]},
    )

    assert response.status_code == 200
    assert response.json()["trip_traveler_id"] == cross_trip_seed["trip_traveler_id"]


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


def test_scan_activity_checkin_uncontrolled_activity_accepts_trip_traveler(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=headers,
        json={"qr_payload": seed["second_qr_payload"]},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "checked_in"
    assert response.json()["trip_traveler_id"] == seed["second_trip_traveler_id"]


def test_scan_activity_checkin_controlled_activity_accepts_allowed_traveler(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))

    async def _seed_allowed_participant():
        async with session_factory() as session:
            session.add(
                ActivityParticipant(
                    trip_activity_id=seed["activity_id"],
                    trip_traveler_id=seed["trip_traveler_id"],
                    status="allowed",
                )
            )
            await session.commit()

    asyncio.run(_seed_allowed_participant())
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=headers,
        json={"qr_payload": seed["qr_payload"]},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "checked_in"


def test_scan_activity_checkin_controlled_activity_rejects_unlisted_traveler_and_audits(
    seeded_client,
    session_factory,
):
    seed = asyncio.run(_seed_staff_trip_with_tasks(session_factory))

    async def _seed_allowed_participant():
        async with session_factory() as session:
            session.add(
                ActivityParticipant(
                    trip_activity_id=seed["activity_id"],
                    trip_traveler_id=seed["trip_traveler_id"],
                    status="allowed",
                )
            )
            await session.commit()

    asyncio.run(_seed_allowed_participant())
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.post(
        f"/me/staff/activities/{seed['activity_id']}/checkins/scan",
        headers=headers,
        json={"qr_payload": seed["second_qr_payload"]},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Traveler is not authorized for this activity"

    async def _load_event_count():
        async with session_factory() as session:
            return await session.scalar(
                select(func.count())
                .select_from(ActivityCheckinScanEvent)
                .where(
                    ActivityCheckinScanEvent.trip_activity_id == seed["activity_id"],
                    ActivityCheckinScanEvent.trip_traveler_id == seed["second_trip_traveler_id"],
                    ActivityCheckinScanEvent.status == "not_authorized_for_activity",
                )
            )

    assert asyncio.run(_load_event_count()) == 1


def test_scan_activity_checkin_duplicate_creates_audit_event(
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

    async def _load_event_statuses():
        async with session_factory() as session:
            rows = await session.execute(
                select(ActivityCheckinScanEvent.status)
                .where(
                    ActivityCheckinScanEvent.trip_activity_id == seed["activity_id"],
                    ActivityCheckinScanEvent.trip_traveler_id == seed["trip_traveler_id"],
                )
                .order_by(ActivityCheckinScanEvent.created_at)
            )
            return [row[0] for row in rows.all()]

    assert asyncio.run(_load_event_statuses()) == ["checked_in", "already_checked_in"]

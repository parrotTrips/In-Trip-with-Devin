import asyncio
from datetime import date

from sqlalchemy import text

from app.db.models.staff import StaffTask
from app.db.models.trip import TripActivity, TripPhase, TripTraveler
from app.db.models.user import User


async def _seed_staff_trip_with_tasks(session_factory):
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
        session.add_all([staff, other_staff])
        await session.flush()
        session.add(TripTraveler(wetravel_trip_uuid="staff-route-test", user_id=staff.id))

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
        await session.commit()


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

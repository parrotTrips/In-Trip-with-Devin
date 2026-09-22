import asyncio
from datetime import date

from sqlalchemy import text

from app.db.models.user import User

TRIP = "roteiro-test"


async def _seed(session_factory):
    async with session_factory() as session:
        await session.execute(
            text("INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                 " VALUES (:u, 'Roteiro Test', 'Brazil', :sd, :ed)"
                 " ON CONFLICT (trip_uuid) DO NOTHING"),
            {"u": TRIP, "sd": date(2027, 7, 1), "ed": date(2027, 7, 10)},
        )
        session.add(User(phone="+5511555000001", full_name="Admin", status="active", role="admin"))
        await session.commit()


def _admin(client) -> dict:
    otp = client.post("/auth/request-otp", json={"phone": "+5511555000001"})
    verify = client.post(
        "/auth/verify-otp",
        json={"phone": "+5511555000001", "code": otp.json()["debug_code"]},
    )
    return {"Authorization": f"Bearer {verify.json()['access_token']}"}


def _create_day(client, headers, title="Dia 1") -> str:
    res = client.post(
        f"/console/trips/{TRIP}/days",
        headers=headers,
        json={"title": title, "short_description": ""},
    )
    assert res.status_code == 200, res.text
    return res.json()["id"]


def _create_activity(client, headers, day_id, **fields) -> str:
    body = {"name": "Corcovado", "activity_type": "included", **fields}
    res = client.post(f"/console/days/{day_id}/activities", headers=headers, json=body)
    assert res.status_code == 200, res.text
    return res.json()["id"]


def test_creating_a_day_makes_an_in_trip_phase(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    day_id = _create_day(client, headers)

    async def _phase_type():
        async with session_factory() as session:
            return await session.scalar(
                text("SELECT phase_type FROM trip_phases WHERE id = CAST(:p AS uuid)"),
                {"p": day_id},
            )

    assert asyncio.run(_phase_type()) == "in-trip"

    # E não aparece entre as fases pré-trip
    phases = client.get(f"/console/trips/{TRIP}/phases", headers=headers).json()["phases"]
    assert phases == []


def test_days_are_listed_with_their_activities(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)
    day_id = _create_day(client, headers)
    _create_activity(client, headers, day_id, name="Cristo")

    res = client.get(f"/console/trips/{TRIP}/days", headers=headers)

    assert res.status_code == 200
    days = res.json()["days"]
    assert len(days) == 1
    assert days[0]["title"] == "Dia 1"
    assert [a["name"] for a in days[0]["activities"]] == ["Cristo"]


def test_editing_an_activity_keeps_its_id_and_checkins(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)
    day_id = _create_day(client, headers)
    activity_id = _create_activity(client, headers, day_id, name="Antigo")

    async def _add_checkin():
        async with session_factory() as session:
            user_id = await session.scalar(
                text("INSERT INTO users (id, phone, status, role, created_at, updated_at)"
                     " VALUES (gen_random_uuid(), '+5511555000099', 'active', 'traveler',"
                     "         now(), now()) RETURNING id")
            )
            tt_id = await session.scalar(
                text("INSERT INTO trip_travelers (id, wetravel_trip_uuid, user_id)"
                     " VALUES (gen_random_uuid(), :u, :uid) RETURNING id"),
                {"u": TRIP, "uid": user_id},
            )
            await session.execute(
                text("INSERT INTO activity_checkins (id, trip_activity_id, trip_traveler_id,"
                     " scanned_by_user_id, scan_number, checked_in_at)"
                     " VALUES (gen_random_uuid(), CAST(:a AS uuid), :tt, :uid, 1, now())"),
                {"a": activity_id, "tt": tt_id, "uid": user_id},
            )
            await session.commit()

    asyncio.run(_add_checkin())

    res = client.patch(
        f"/console/activities/{activity_id}", headers=headers, json={"name": "Novo"}
    )

    assert res.status_code == 200

    async def _state():
        async with session_factory() as session:
            return (
                await session.scalar(
                    text("SELECT name FROM trip_activities WHERE id = CAST(:a AS uuid)"),
                    {"a": activity_id},
                ),
                await session.scalar(
                    text("SELECT count(*) FROM activity_checkins"
                         " WHERE trip_activity_id = CAST(:a AS uuid)"),
                    {"a": activity_id},
                ),
            )

    assert asyncio.run(_state()) == ("Novo", 1)


def test_deleting_an_activity_without_checkins_works(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)
    day_id = _create_day(client, headers)
    activity_id = _create_activity(client, headers, day_id)

    assert client.delete(f"/console/activities/{activity_id}", headers=headers).status_code == 200

    days = client.get(f"/console/trips/{TRIP}/days", headers=headers).json()["days"]
    assert days[0]["activities"] == []


def test_deleting_an_activity_with_scans_is_refused(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)
    day_id = _create_day(client, headers)
    activity_id = _create_activity(client, headers, day_id)

    async def _add_scan():
        async with session_factory() as session:
            user_id = await session.scalar(
                text("INSERT INTO users (id, phone, status, role, created_at, updated_at)"
                     " VALUES (gen_random_uuid(), '+5511555000098', 'active', 'staff',"
                     "         now(), now()) RETURNING id")
            )
            await session.execute(
                text("INSERT INTO activity_checkin_scan_events (id, trip_activity_id,"
                     " scanned_by_user_id, status, created_at)"
                     " VALUES (gen_random_uuid(), CAST(:a AS uuid), :uid, 'success', now())"),
                {"a": activity_id, "uid": user_id},
            )
            await session.commit()

    asyncio.run(_add_scan())

    res = client.delete(f"/console/activities/{activity_id}", headers=headers)

    assert res.status_code == 409
    assert "scan" in res.json()["detail"].lower() or "check" in res.json()["detail"].lower()

    days = client.get(f"/console/trips/{TRIP}/days", headers=headers).json()["days"]
    assert len(days[0]["activities"]) == 1


def test_activity_type_must_be_known(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)
    day_id = _create_day(client, headers)

    res = client.post(
        f"/console/days/{day_id}/activities",
        headers=headers,
        json={"name": "X", "activity_type": "teleporte"},
    )

    assert res.status_code == 422
    assert "activity_type" in res.json()["detail"]


def test_reordering_activities_sets_sort_order(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)
    day_id = _create_day(client, headers)
    first = _create_activity(client, headers, day_id, name="A")
    second = _create_activity(client, headers, day_id, name="B")

    res = client.put(
        f"/console/days/{day_id}/activities/order",
        headers=headers,
        json={"activity_ids": [second, first]},
    )

    assert res.status_code == 200
    days = client.get(f"/console/trips/{TRIP}/days", headers=headers).json()["days"]
    assert [a["name"] for a in days[0]["activities"]] == ["B", "A"]

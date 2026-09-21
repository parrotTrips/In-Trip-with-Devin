import asyncio
from datetime import date

from sqlalchemy import text

from app.db.models.user import User


async def _seed_admin_and_trip(session_factory):
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": "console-test",
                "title": "Console Test Trip",
                "dest": "Brazil",
                "sd": date(2027, 7, 1),
                "ed": date(2027, 7, 10),
            },
        )
        session.add_all([
            User(phone="+5511777000001", full_name="Admin", status="active", role="admin"),
            User(phone="+5511777000002", full_name="Trav", status="active", role="traveler"),
        ])
        await session.commit()


def _auth(client, phone: str) -> dict:
    otp_res = client.post("/auth/request-otp", json={"phone": phone})
    verify_res = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_res.json()["debug_code"]},
    )
    return {"Authorization": f"Bearer {verify_res.json()['access_token']}"}


def test_console_trips_requires_a_token(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    assert client.get("/console/trips").status_code == 401


def test_console_trips_rejects_non_admin(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000002")
    assert client.get("/console/trips", headers=headers).status_code == 403


def test_console_trips_lists_trips_for_admin(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    res = client.get("/console/trips", headers=headers)
    assert res.status_code == 200
    assert "console-test" in [t["trip_uuid"] for t in res.json()["trips"]]

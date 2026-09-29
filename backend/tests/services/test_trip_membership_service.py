import asyncio
from datetime import date, timedelta

from sqlalchemy import text

from app.db.models.user import User


async def _seed_memberships(session_factory):
    today = date.today()
    trips = [
        (
            "trip-ended",
            "Viagem encerrada",
            "Recife",
            today - timedelta(days=10),
            today - timedelta(days=1),
        ),
        (
            "trip-current",
            "Viagem atual",
            "Rio de Janeiro",
            today - timedelta(days=2),
            today + timedelta(days=2),
        ),
        (
            "trip-future-later",
            "Viagem futura distante",
            "Lisboa",
            today + timedelta(days=20),
            today + timedelta(days=25),
        ),
        (
            "trip-future-next",
            "Próxima viagem",
            "Salvador",
            today + timedelta(days=5),
            today + timedelta(days=8),
        ),
    ]

    async with session_factory() as session:
        user = User(
            phone="+5511999999910",
            full_name="Pessoa com várias viagens",
            status="active",
            role="admin",
        )
        unrelated_user = User(
            phone="+5511999999911",
            full_name="Pessoa sem associação",
            status="active",
            role="staff",
        )
        session.add_all([user, unrelated_user])
        await session.flush()

        for trip_id, title, destination, start_date, end_date in trips:
            await session.execute(
                text(
                    """
                    INSERT INTO wetravel_trips
                        (trip_uuid, title, destination, start_date, end_date)
                    VALUES (:trip_id, :title, :destination, :start_date, :end_date)
                    """
                ),
                {
                    "trip_id": trip_id,
                    "title": title,
                    "destination": destination,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )
            await session.execute(
                text(
                    """
                    INSERT INTO trip_travelers (id, wetravel_trip_uuid, user_id)
                    VALUES (gen_random_uuid(), :trip_id, :user_id)
                    """
                ),
                {"trip_id": trip_id, "user_id": user.id},
            )

        await session.execute(
            text(
                """
                INSERT INTO trip_staff
                    (id, wetravel_trip_uuid, user_id, function, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), 'trip-current', :user_id, 'Guia', now(), now()),
                    (gen_random_uuid(), 'trip-future-later', :user_id, 'Guia', now(), now())
                """
            ),
            {"user_id": user.id},
        )
        await session.commit()
        return str(user.id), str(unrelated_user.id)


def test_list_eligible_trips_filters_orders_and_derives_role_per_trip(session_factory):
    from app.services.trip_membership_service import list_eligible_trips

    user_id, _ = asyncio.run(_seed_memberships(session_factory))

    async def run():
        async with session_factory() as session:
            return await list_eligible_trips(user_id, session)

    trips = asyncio.run(run())

    assert [trip["trip_id"] for trip in trips] == [
        "trip-current",
        "trip-future-next",
        "trip-future-later",
    ]
    assert trips == [
        {
            "trip_id": "trip-current",
            "title": "Viagem atual",
            "destination": "Rio de Janeiro",
            "start_date": date.today() - timedelta(days=2),
            "end_date": date.today() + timedelta(days=2),
            "role": "staff",
            "is_current": True,
        },
        {
            "trip_id": "trip-future-next",
            "title": "Próxima viagem",
            "destination": "Salvador",
            "start_date": date.today() + timedelta(days=5),
            "end_date": date.today() + timedelta(days=8),
            "role": "traveler",
            "is_current": False,
        },
        {
            "trip_id": "trip-future-later",
            "title": "Viagem futura distante",
            "destination": "Lisboa",
            "start_date": date.today() + timedelta(days=20),
            "end_date": date.today() + timedelta(days=25),
            "role": "staff",
            "is_current": False,
        },
    ]


def test_get_eligible_trip_membership_reuses_eligibility_and_association_rules(session_factory):
    from app.services.trip_membership_service import get_eligible_trip_membership

    user_id, unrelated_user_id = asyncio.run(_seed_memberships(session_factory))

    async def run():
        async with session_factory() as session:
            current = await get_eligible_trip_membership(user_id, "trip-current", session)
            ended = await get_eligible_trip_membership(user_id, "trip-ended", session)
            unrelated = await get_eligible_trip_membership(
                unrelated_user_id, "trip-current", session
            )
            return current, ended, unrelated

    current, ended, unrelated = asyncio.run(run())

    assert current is not None
    assert current["trip_id"] == "trip-current"
    assert current["role"] == "staff"
    assert current["is_current"] is True
    assert ended is None
    assert unrelated is None


def test_eligibility_uses_sao_paulo_date_regardless_of_database_timezone(session_factory):
    from app.services.trip_membership_service import (
        list_eligible_trips,
        require_trip_membership,
    )

    async def run():
        async with session_factory() as session:
            user = User(phone="+5511999999912", status="active", role="traveler")
            session.add(user)
            await session.flush()
            sao_paulo_today = await session.scalar(
                text(
                    "SELECT (CURRENT_TIMESTAMP AT TIME ZONE "
                    "'America/Sao_Paulo')::date"
                )
            )
            await session.execute(
                text(
                    """
                    INSERT INTO wetravel_trips
                        (trip_uuid, title, destination, start_date, end_date)
                    VALUES
                        ('trip-timezone-boundary', 'Último dia', 'São Paulo',
                         :today, :today)
                    """
                ),
                {"today": sao_paulo_today},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO trip_travelers (id, wetravel_trip_uuid, user_id)
                    VALUES (gen_random_uuid(), 'trip-timezone-boundary', :user_id)
                    """
                ),
                {"user_id": user.id},
            )
            await session.commit()

            # Pick a session timezone whose calendar date differs right now, so
            # replacing the explicit São Paulo expression with CURRENT_DATE
            # would make this test fail at every hour of the day.
            timezone_dates = (
                await session.execute(
                    text(
                        """
                        SELECT
                          (CURRENT_TIMESTAMP AT TIME ZONE 'Pacific/Kiritimati')::date
                            AS kiritimati,
                          (CURRENT_TIMESTAMP AT TIME ZONE 'Pacific/Honolulu')::date
                            AS honolulu
                        """
                    )
                )
            ).mappings().one()
            session_timezone = next(
                zone
                for zone, zone_date in (
                    ("Pacific/Kiritimati", timezone_dates["kiritimati"]),
                    ("Pacific/Honolulu", timezone_dates["honolulu"]),
                )
                if zone_date != sao_paulo_today
            )
            await session.execute(text(f"SET TIME ZONE '{session_timezone}'"))
            assert await session.scalar(text("SELECT CURRENT_DATE")) != sao_paulo_today
            trips = await list_eligible_trips(str(user.id), session)
            membership = await require_trip_membership(
                str(user.id), "trip-timezone-boundary", session
            )
            return trips, membership

    trips, membership = asyncio.run(run())
    assert [trip["trip_id"] for trip in trips] == ["trip-timezone-boundary"]
    assert membership.wetravel_trip_uuid == "trip-timezone-boundary"

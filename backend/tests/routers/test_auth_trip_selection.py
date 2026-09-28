import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

from jose import jwt
from sqlalchemy import text


JWT_SECRET = "test-secret-key-for-testing-only"


async def _seed_trip_choices(session_factory):
    async with session_factory() as session:
        user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        await session.execute(
            text(
                """
                INSERT INTO users (id, phone, full_name, status, role, created_at, updated_at)
                VALUES
                  (:user_id, '+5511999999920', 'Multi Trip', 'active', 'traveler', now(), now()),
                  (:other_id, '+5511999999921', 'Other', 'active', 'traveler', now(), now())
                """
            ),
            {"user_id": user_id, "other_id": other_user_id},
        )
        today = date.today()
        for trip_id, start_date, end_date in [
            ("trip-traveler", today, today + timedelta(days=2)),
            ("trip-staff", today + timedelta(days=3), today + timedelta(days=6)),
            ("trip-ended", today - timedelta(days=5), today - timedelta(days=1)),
            ("trip-unrelated", today + timedelta(days=4), today + timedelta(days=7)),
        ]:
            await session.execute(
                text(
                    """
                    INSERT INTO wetravel_trips
                      (trip_uuid, title, destination, start_date, end_date)
                    VALUES (:trip_id, :title, 'Destino', :start_date, :end_date)
                    """
                ),
                {"trip_id": trip_id, "title": trip_id, "start_date": start_date, "end_date": end_date},
            )
        for trip_id in ["trip-traveler", "trip-staff", "trip-ended"]:
            await session.execute(
                text(
                    """
                    INSERT INTO trip_travelers (id, wetravel_trip_uuid, user_id)
                    VALUES (gen_random_uuid(), :trip_id, :user_id)
                    """
                ),
                {"trip_id": trip_id, "user_id": user_id},
            )
        await session.execute(
            text(
                """
                INSERT INTO trip_travelers (id, wetravel_trip_uuid, user_id)
                VALUES (gen_random_uuid(), 'trip-unrelated', :other_id)
                """
            ),
            {"other_id": other_user_id},
        )
        await session.execute(
            text(
                """
                INSERT INTO trip_staff
                  (id, wetravel_trip_uuid, user_id, function, created_at, updated_at)
                VALUES (gen_random_uuid(), 'trip-staff', :user_id, 'Guia', now(), now())
                """
            ),
            {"user_id": user_id},
        )
        await session.commit()
        return str(user_id)


def _token(user_id, *, token_type="trip_selection", **claims):
    return jwt.encode(
        {
            "sub": user_id,
            "phone": "+5511999999920",
            "token_type": token_type,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
            **claims,
        },
        JWT_SECRET,
        algorithm="HS256",
    )


def test_list_trips_accepts_selection_and_session_tokens(client, session_factory):
    user_id = asyncio.run(_seed_trip_choices(session_factory))

    for token in [
        _token(user_id),
        _token(user_id, token_type="session", trip_id="trip-traveler", role="traveler"),
    ]:
        response = client.get("/auth/trips", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert [trip["trip_id"] for trip in response.json()["trips"]] == [
            "trip-traveler",
            "trip-staff",
        ]


def test_select_trip_returns_session_token_with_per_trip_staff_role(client, session_factory):
    user_id = asyncio.run(_seed_trip_choices(session_factory))
    response = client.post(
        "/auth/select-trip",
        json={"trip_id": "trip-staff"},
        headers={"Authorization": f"Bearer {_token(user_id)}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "trip_selected"
    assert body["name"] == "Multi Trip"
    assert body["active_trip"]["trip_id"] == "trip-staff"
    assert body["active_trip"]["role"] == "staff"
    claims = jwt.decode(body["access_token"], JWT_SECRET, algorithms=["HS256"])
    assert claims["token_type"] == "session"
    assert claims["trip_id"] == "trip-staff"
    assert claims["role"] == "staff"


def test_select_trip_rejects_ended_and_unrelated_trips(client, session_factory):
    user_id = asyncio.run(_seed_trip_choices(session_factory))
    headers = {"Authorization": f"Bearer {_token(user_id)}"}

    for trip_id in ["trip-ended", "trip-unrelated"]:
        response = client.post("/auth/select-trip", json={"trip_id": trip_id}, headers=headers)
        assert response.status_code == 403
        assert response.json() == {"detail": "Trip not available"}


def test_select_trip_caps_new_session_at_original_identity_expiry(client, session_factory):
    """A session must not renew forever: exchanging a token near the end of its
    14-day identity lifetime (auth_time, set once at verify-otp) must not reset
    the clock — the new session's exp stays capped at auth_time + 14 days.
    """
    user_id = asyncio.run(_seed_trip_choices(session_factory))
    now = datetime.now(timezone.utc)
    original_auth_time = now - timedelta(days=13)
    identity_cap = original_auth_time + timedelta(days=14)  # 1 day from now
    token = _token(
        user_id,
        auth_time=int(original_auth_time.timestamp()),
        exp=now + timedelta(minutes=10),
    )

    response = client.post(
        "/auth/select-trip",
        json={"trip_id": "trip-staff"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    claims = jwt.decode(
        response.json()["access_token"], JWT_SECRET, algorithms=["HS256"]
    )
    new_exp = datetime.fromtimestamp(claims["exp"], timezone.utc)
    # Must not have been granted a fresh 14-day lifetime from now.
    assert new_exp < now + timedelta(days=2)
    assert abs((new_exp - identity_cap).total_seconds()) < 5
    assert claims["auth_time"] == int(original_auth_time.timestamp())


def test_select_trip_legacy_token_without_auth_time_does_not_extend_lifetime(
    client, session_factory
):
    """A token minted before the auth_time claim existed has no identity
    lifetime to preserve. Deliberate choice: cap the new session at the
    incoming token's own expiry (never grant a fresh 14-day lifetime), and
    stamp an auth_time on the new token so later exchanges of *it* are capped
    normally.
    """
    user_id = asyncio.run(_seed_trip_choices(session_factory))
    now = datetime.now(timezone.utc)
    legacy_exp = now + timedelta(days=2)
    token = _token(user_id, exp=legacy_exp)

    response = client.post(
        "/auth/select-trip",
        json={"trip_id": "trip-staff"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    claims = jwt.decode(
        response.json()["access_token"], JWT_SECRET, algorithms=["HS256"]
    )
    new_exp = datetime.fromtimestamp(claims["exp"], timezone.utc)
    assert abs((new_exp - legacy_exp).total_seconds()) < 5
    assert "auth_time" in claims


def test_trip_choice_routes_reject_missing_expired_or_wrong_type_tokens(client, session_factory):
    user_id = asyncio.run(_seed_trip_choices(session_factory))
    expired = jwt.encode(
        {
            "sub": user_id,
            "phone": "+5511999999920",
            "token_type": "trip_selection",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        JWT_SECRET,
        algorithm="HS256",
    )
    wrong_type = _token(user_id, token_type="password_reset")

    malformed_subject = _token("not-a-uuid")

    for token in [None, expired, wrong_type, malformed_subject]:
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/trips", headers=headers)
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

import asyncio
import uuid
from datetime import date, timedelta
from uuid import UUID

import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy import select, text

from app.db.models.auth import OTPCode
from app.db.models.user import User
from app.services.auth_service import request_otp, verify_otp


async def fake_sender(_phone: str, _code: str) -> bool:
    return False


def fixed_code() -> str:
    return "123456"


def test_typed_token_helpers_issue_distinct_claims(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.JWT_SECRET", "test-secret-for-jwt")
    from app.services import auth_service

    assert hasattr(auth_service, "_create_selection_token")
    assert hasattr(auth_service, "_create_session_token")

    selection_claims = jwt.decode(
        auth_service._create_selection_token("user-1", "+5511999999999"),
        "test-secret-for-jwt",
        algorithms=["HS256"],
    )
    session_claims = jwt.decode(
        auth_service._create_session_token(
            "user-1", "+5511999999999", "trip-1", "staff"
        ),
        "test-secret-for-jwt",
        algorithms=["HS256"],
    )

    assert selection_claims["token_type"] == "trip_selection"
    assert "trip_id" not in selection_claims
    assert session_claims["token_type"] == "session"
    assert session_claims["trip_id"] == "trip-1"
    assert session_claims["role"] == "staff"


async def _seed_user(session, phone: str, role: str = "traveler") -> User:
    user = User(id=uuid.uuid4(), phone=phone, status="active", role=role)
    session.add(user)
    await session.commit()
    return user


async def _seed_trip(session, user: User, trip_id: str, *, days_from_now: int, staff=False):
    start_date = date.today() + timedelta(days=days_from_now)
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
            "title": f"Trip {trip_id}",
            "destination": "Destino",
            "start_date": start_date,
            "end_date": start_date + timedelta(days=3),
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
    if staff:
        await session.execute(
            text(
                """
                INSERT INTO trip_staff
                    (id, wetravel_trip_uuid, user_id, function, created_at, updated_at)
                VALUES (gen_random_uuid(), :trip_id, :user_id, 'Guia', now(), now())
                """
            ),
            {"trip_id": trip_id, "user_id": user.id},
        )
    await session.commit()


def test_request_otp_generates_and_stores_code(session_factory):
    async def run_test():
        async with session_factory() as session:
            await _seed_user(session, "+5511999999999")
            response = await request_otp(
                "+5511999999999",
                session,
                otp_sender=fake_sender,
                code_generator=fixed_code,
            )

            otp_row = await session.scalar(
                select(OTPCode).order_by(OTPCode.created_at.desc())
            )

            assert response == {
                "message": "OTP generated (WhatsApp delivery failed, showing code for testing)",
                "debug_code": "123456",
            }
            assert otp_row is not None
            assert otp_row.phone == "+5511999999999"
            assert otp_row.code == "123456"
            assert otp_row.used is False

    asyncio.run(run_test())


def test_request_otp_rejects_unauthorized_phone(session_factory):
    async def run_test():
        async with session_factory() as session:
            with pytest.raises(HTTPException) as exc_info:
                await request_otp(
                    "+5500000000000",
                    session,
                    otp_sender=fake_sender,
                    code_generator=fixed_code,
                )
            assert exc_info.value.status_code == 403

    asyncio.run(run_test())


def test_verify_otp_succeeds_for_authorized_user(session_factory):
    async def run_test():
        async with session_factory() as session:
            await _seed_user(session, "+5511888888888")
            await request_otp(
                "+5511888888888",
                session,
                otp_sender=fake_sender,
                code_generator=fixed_code,
            )

            response = await verify_otp("+5511888888888", "123456", session)

            user_row = await session.scalar(select(User).where(User.phone == "+5511888888888"))
            otp_row = await session.scalar(
                select(OTPCode).where(
                    OTPCode.phone == "+5511888888888",
                    OTPCode.code == "123456",
                )
            )

            assert user_row is not None
            assert otp_row is not None
            assert response["user_id"] == str(user_row.id)
            assert response["phone"] == "+5511888888888"
            assert response["status"] == "no_trips"
            assert response["message"] == "No current or future trips available"
            assert "access_token" not in response
            assert UUID(response["user_id"]) == user_row.id
            assert user_row.status == "active"
            assert otp_row.used is True

    asyncio.run(run_test())


def test_verify_otp_selects_only_trip_and_returns_scoped_session_token(
    session_factory, monkeypatch
):
    monkeypatch.setenv("JWT_SECRET", "test-secret-for-jwt")
    import sys
    for mod in list(sys.modules):
        if "app.core.config" in mod or "app.services.auth_service" in mod:
            sys.modules.pop(mod)
    from app.services.auth_service import request_otp, verify_otp

    async def run_test():
        async with session_factory() as session:
            user = await _seed_user(session, "+5511777777777", role="traveler")
            await _seed_trip(session, user, "trip-only", days_from_now=1, staff=True)
            await request_otp(
                "+5511777777777",
                session,
                otp_sender=fake_sender,
                code_generator=fixed_code,
            )
            response = await verify_otp("+5511777777777", "123456", session)

            assert response["status"] == "trip_selected"
            assert response["can_switch_trips"] is False
            assert response["active_trip"]["trip_id"] == "trip-only"
            assert response["active_trip"]["role"] == "staff"
            payload = jwt.decode(
                response["access_token"],
                "test-secret-for-jwt",
                algorithms=["HS256"],
            )
            assert payload["phone"] == "+5511777777777"
            assert payload["token_type"] == "session"
            assert payload["trip_id"] == "trip-only"
            assert payload["role"] == "staff"
            assert "sub" in payload
            assert "exp" in payload

    asyncio.run(run_test())


def test_verify_otp_requires_selection_for_multiple_trips(session_factory, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-for-jwt")
    import sys
    for mod in list(sys.modules):
        if "app.core.config" in mod or "app.services.auth_service" in mod:
            sys.modules.pop(mod)
    from app.services.auth_service import request_otp, verify_otp

    async def run_test():
        async with session_factory() as session:
            user = await _seed_user(session, "+5511777777778")
            await _seed_trip(session, user, "trip-first", days_from_now=1)
            await _seed_trip(session, user, "trip-second", days_from_now=5, staff=True)
            await request_otp(
                user.phone,
                session,
                otp_sender=fake_sender,
                code_generator=fixed_code,
            )

            response = await verify_otp(user.phone, "123456", session)

            assert response["status"] == "selection_required"
            assert [trip["trip_id"] for trip in response["trips"]] == [
                "trip-first",
                "trip-second",
            ]
            assert response["user_id"] == str(user.id)
            assert response["phone"] == user.phone
            assert response["name"] is None
            assert "access_token" not in response
            payload = jwt.decode(
                response["selection_token"],
                "test-secret-for-jwt",
                algorithms=["HS256"],
            )
            assert payload["sub"] == str(user.id)
            assert payload["phone"] == user.phone
            assert payload["token_type"] == "trip_selection"
            assert "trip_id" not in payload
            assert "role" not in payload
            assert "exp" in payload

    asyncio.run(run_test())


def test_verify_otp_authenticates_admin_without_trip_membership(
    session_factory, monkeypatch
):
    monkeypatch.setenv("JWT_SECRET", "test-secret-for-jwt")
    import sys
    for mod in list(sys.modules):
        if "app.core.config" in mod or "app.services.auth_service" in mod:
            sys.modules.pop(mod)
    from app.services.auth_service import request_otp, verify_otp

    async def run_test():
        async with session_factory() as session:
            admin = await _seed_user(session, "+5511777777779", role="admin")
            await request_otp(
                admin.phone,
                session,
                otp_sender=fake_sender,
                code_generator=fixed_code,
            )

            response = await verify_otp(admin.phone, "123456", session)

            assert response["status"] == "admin_authenticated"
            assert response["role"] == "admin"
            assert response["user_id"] == str(admin.id)
            claims = jwt.decode(
                response["access_token"],
                "test-secret-for-jwt",
                algorithms=["HS256"],
            )
            assert claims["token_type"] == "admin"
            assert claims["role"] == "admin"
            assert "trip_id" not in claims

    asyncio.run(run_test())

import asyncio
import os
from uuid import UUID

from jose import jwt
from sqlalchemy import select

from app.db.models.auth import OTPCode
from app.db.models.user import User
from app.services.auth_service import request_otp, verify_otp


async def fake_sender(_phone: str, _code: str) -> bool:
    return False


def fixed_code() -> str:
    return "123456"


def test_request_otp_generates_and_stores_code(session_factory):
    async def run_test():
        async with session_factory() as session:
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


def test_verify_otp_creates_user_on_first_login(session_factory):
    async def run_test():
        async with session_factory() as session:
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
            assert response["name"] is None
            assert response["message"] == "Login successful"
            assert "access_token" in response
            assert UUID(response["user_id"]) == user_row.id
            assert user_row.status == "active"
            assert otp_row.used is True

    asyncio.run(run_test())


def test_verify_otp_returns_access_token(session_factory, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-for-jwt")
    import sys
    for mod in list(sys.modules):
        if "app.core.config" in mod or "app.services.auth_service" in mod:
            sys.modules.pop(mod)
    from app.services.auth_service import request_otp, verify_otp

    async def run_test():
        async with session_factory() as session:
            await request_otp(
                "+5511777777777",
                session,
                otp_sender=fake_sender,
                code_generator=fixed_code,
            )
            response = await verify_otp("+5511777777777", "123456", session)

            assert "access_token" in response
            payload = jwt.decode(
                response["access_token"],
                "test-secret-for-jwt",
                algorithms=["HS256"],
            )
            assert payload["phone"] == "+5511777777777"
            assert "sub" in payload
            assert "exp" in payload

    asyncio.run(run_test())

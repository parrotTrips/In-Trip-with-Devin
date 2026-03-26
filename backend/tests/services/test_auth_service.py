import asyncio
import sqlite3

from app.db.database import init_db
from app.services.auth_service import request_otp, verify_otp


async def fake_sender(_phone: str, _code: str) -> bool:
    return False


def fixed_code() -> str:
    return "123456"


def test_request_otp_generates_and_stores_code(tmp_path):
    database_path = tmp_path / "auth.db"
    asyncio.run(init_db(database_path))

    response = asyncio.run(
        request_otp(
            "+5511999999999",
            database_path=database_path,
            otp_sender=fake_sender,
            code_generator=fixed_code,
        )
    )

    assert response == {
        "message": "OTP generated (WhatsApp delivery failed, showing code for testing)",
        "debug_code": "123456",
    }

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT phone, code, used FROM otp_codes ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row == ("+5511999999999", "123456", 0)


def test_verify_otp_creates_user_on_first_login(tmp_path):
    database_path = tmp_path / "auth.db"
    asyncio.run(init_db(database_path))
    asyncio.run(
        request_otp(
            "+5511888888888",
            database_path=database_path,
            otp_sender=fake_sender,
            code_generator=fixed_code,
        )
    )

    response = asyncio.run(
        verify_otp("+5511888888888", "123456", database_path=database_path)
    )

    assert response == {
        "user_id": 1,
        "phone": "+5511888888888",
        "name": None,
        "message": "Login successful",
    }

    with sqlite3.connect(database_path) as connection:
        user_row = connection.execute(
            "SELECT id, phone, name FROM users WHERE phone = ?",
            ("+5511888888888",),
        ).fetchone()
        otp_row = connection.execute(
            "SELECT used FROM otp_codes WHERE phone = ? AND code = ?",
            ("+5511888888888", "123456"),
        ).fetchone()

    assert user_row == (1, "+5511888888888", None)
    assert otp_row == (1,)

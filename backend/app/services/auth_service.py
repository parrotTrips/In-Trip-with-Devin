"""Authentication service functions."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Awaitable, Callable

import aiosqlite
import httpx
from fastapi import HTTPException

from app.core.config import (
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_URL,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_TEMPLATE_NAME,
)
from app.db.database import connect_to_database


async def send_whatsapp_otp(phone: str, code: str) -> bool:
    """Send an OTP through the configured WhatsApp Business API template."""
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        return False

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone.replace("+", "").replace(" ", "").replace("-", ""),
        "type": "template",
        "template": {
            "name": WHATSAPP_TEMPLATE_NAME,
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": code}],
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [{"type": "text", "text": code}],
                },
            ],
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WHATSAPP_API_URL,
                headers=headers,
                json=payload,
                timeout=10.0,
            )
    except Exception:
        return False

    return response.status_code == 200


async def request_otp(
    phone: str,
    database_path: str | Path | None = None,
    otp_sender: Callable[[str, str], Awaitable[bool]] = send_whatsapp_otp,
    code_generator: Callable[[], str] | None = None,
) -> dict:
    """Generate an OTP, persist it and attempt WhatsApp delivery."""
    generator = code_generator or (lambda: str(random.randint(100000, 999999)))
    code = generator()
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    async with connect_to_database(database_path) as db:
        await db.execute(
            "INSERT INTO otp_codes (phone, code, expires_at) VALUES (?, ?, ?)",
            (phone, code, expires_at.isoformat()),
        )
        await db.commit()

    whatsapp_sent = await otp_sender(phone, code)
    response_data = {"message": "OTP sent successfully"}
    if not whatsapp_sent:
        response_data["message"] = (
            "OTP generated (WhatsApp delivery failed, showing code for testing)"
        )
        response_data["debug_code"] = code

    return response_data


async def verify_otp(
    phone: str,
    code: str,
    database_path: str | Path | None = None,
) -> dict:
    """Validate an OTP and create the user on first successful login."""
    async with connect_to_database(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM otp_codes
            WHERE phone = ? AND code = ? AND used = FALSE
            ORDER BY created_at DESC LIMIT 1
            """,
            (phone, code),
        )
        otp = await cursor.fetchone()

        if not otp:
            raise HTTPException(status_code=400, detail="Invalid OTP code")

        if datetime.fromisoformat(otp["expires_at"]) < datetime.now(UTC):
            raise HTTPException(status_code=400, detail="OTP code expired")

        await db.execute("UPDATE otp_codes SET used = TRUE WHERE id = ?", (otp["id"],))

        cursor = await db.execute("SELECT * FROM users WHERE phone = ?", (phone,))
        user = await cursor.fetchone()
        if not user:
            await db.execute("INSERT INTO users (phone) VALUES (?)", (phone,))
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE phone = ?", (phone,))
            user = await cursor.fetchone()
        else:
            await db.commit()

    return {
        "user_id": user["id"],
        "phone": user["phone"],
        "name": user["name"],
        "message": "Login successful",
    }

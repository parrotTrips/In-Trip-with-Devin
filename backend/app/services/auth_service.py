"""Authentication service functions."""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Awaitable, Callable

import httpx
from fastapi import HTTPException
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import (
    JWT_ALGORITHM,
    JWT_EXPIRY_DAYS,
    JWT_SECRET,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_URL,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_TEMPLATE_LANGUAGE,
    WHATSAPP_TEMPLATE_NAME,
)
from app.db.models.auth import OTPCode
from app.db.models.user import User


def _create_access_token(user_id: str, phone: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=JWT_EXPIRY_DAYS)
    payload = {"sub": user_id, "phone": phone, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def send_whatsapp_otp(phone: str, code: str) -> bool:
    """Send an OTP via WhatsApp Cloud API.

    Uses a plain text message while the intripauth template is pending approval.
    Switch WHATSAPP_USE_TEMPLATE=true in .env once the template is approved.
    """
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        return False

    to = phone.replace("+", "").replace(" ", "").replace("-", "")
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    if WHATSAPP_TEMPLATE_NAME == "intripauth":
        # Production path: Authentication template with copy-code button.
        payload: dict = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": "intripauth",
                "language": {"code": WHATSAPP_TEMPLATE_LANGUAGE},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": code}]},
                    {"type": "button", "sub_type": "url", "index": "0",
                     "parameters": [{"type": "text", "text": code}]},
                ],
            },
        }
    else:
        # Temporary path: plain text message while template is not yet approved.
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": (
                    f"Seu código de verificação para logar no app da Parrot Trips "
                    f"é {code}. Válido por 10 minutos."
                )
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
    session: AsyncSession,
    otp_sender: Callable[[str, str], Awaitable[bool]] = send_whatsapp_otp,
    code_generator: Callable[[], str] | None = None,
) -> dict:
    """Generate an OTP, persist it and attempt WhatsApp delivery."""
    generator = code_generator or (lambda: str(random.randint(100000, 999999)))
    code = generator()
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    session.add(OTPCode(phone=phone, code=code, expires_at=expires_at))
    await session.commit()

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
    session: AsyncSession,
) -> dict:
    """Validate an OTP, create the user on first login, and return a JWT."""
    otp = await session.scalar(
        select(OTPCode)
        .where(
            OTPCode.phone == phone,
            OTPCode.code == code,
            OTPCode.used.is_(False),
        )
        .order_by(OTPCode.created_at.desc())
        .limit(1)
    )
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    if otp.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="OTP code expired")

    otp.used = True

    user = await session.scalar(select(User).where(User.phone == phone))
    if not user:
        user = User(
            id=uuid.uuid4(),
            phone=phone,
            full_name=None,
            email=None,
            status="active",
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)

    access_token = _create_access_token(str(user.id), user.phone)

    return {
        "user_id": str(user.id),
        "phone": user.phone,
        "name": user.full_name,
        "message": "Login successful",
        "access_token": access_token,
    }

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
    JWT_SELECTION_EXPIRY_MINUTES,
    JWT_SECRET,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_URL,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_TEMPLATE_LANGUAGE,
    WHATSAPP_TEMPLATE_NAME,
)
from app.core.logger import log, log_erro
from app.db.models.auth import OTPCode
from app.db.models.user import User
from app.services.trip_membership_service import list_eligible_trips


def _encode_token(payload: dict, expires_at: datetime) -> str:
    payload = {**payload, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _create_selection_token(
    user_id: str, phone: str, *, auth_time: datetime | None = None
) -> str:
    """A short-lived (15 min) token permitting only listing/selecting trips.

    ``auth_time`` marks when the person actually completed OTP verification —
    the start of their 14-day identity lifetime. It defaults to now, since a
    selection token is only ever minted fresh, right after OTP verification.
    """
    auth_time = auth_time or datetime.now(UTC)
    return _encode_token(
        {
            "sub": user_id,
            "phone": phone,
            "token_type": "trip_selection",
            "auth_time": int(auth_time.timestamp()),
        },
        datetime.now(UTC) + timedelta(minutes=JWT_SELECTION_EXPIRY_MINUTES),
    )


def _create_session_token(
    user_id: str,
    phone: str,
    trip_id: str,
    role: str,
    *,
    auth_time: datetime | None = None,
    expires_at: datetime | None = None,
) -> str:
    """A trip-scoped session token.

    ``auth_time`` is the moment the person's identity was last established via
    OTP — it is carried through every later trip selection/switch so a session
    (or a stolen token) cannot renew forever by re-selecting a trip every few
    days. It defaults to now: called directly (e.g. from tests, or the
    single-eligible-trip auto-selection path in ``verify_otp``), a session
    starts a fresh 14-day identity lifetime, same as before this change.

    ``expires_at`` lets a caller pin an exact expiry (used for the legacy
    fallback in ``select_trip`` — see ``app.routers.auth``) instead of deriving
    it from ``auth_time``.
    """
    auth_time = auth_time or datetime.now(UTC)
    return _encode_token(
        {
            "sub": user_id,
            "phone": phone,
            "token_type": "session",
            "trip_id": trip_id,
            "role": role,
            "auth_time": int(auth_time.timestamp()),
        },
        expires_at or (auth_time + timedelta(days=JWT_EXPIRY_DAYS)),
    )


def _create_admin_token(user_id: str, phone: str) -> str:
    return _encode_token(
        {
            "sub": user_id,
            "phone": phone,
            "token_type": "admin",
            "role": "admin",
        },
        datetime.now(UTC) + timedelta(days=JWT_EXPIRY_DAYS),
    )


def create_trip_session_payload(
    user_id: str,
    phone: str,
    name: str | None,
    membership: dict,
    can_switch_trips: bool,
    *,
    auth_time: datetime | None = None,
    expires_at: datetime | None = None,
) -> dict:
    """Build the response and scoped JWT for one selected membership.

    ``auth_time``/``expires_at``: see ``_create_session_token``. Omitted by
    ``verify_otp`` (a fresh identity lifetime starts here); passed through by
    ``POST /auth/select-trip`` so exchanging a token never resets the clock.
    """
    return {
        "status": "trip_selected",
        "user_id": user_id,
        "phone": phone,
        "name": name,
        "role": membership["role"],
        "message": "Login successful",
        "access_token": _create_session_token(
            user_id,
            phone,
            membership["trip_id"],
            membership["role"],
            auth_time=auth_time,
            expires_at=expires_at,
        ),
        "active_trip": membership,
        "can_switch_trips": can_switch_trips,
    }


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
    except Exception as exc:
        log_erro("whatsapp_excecao", telefone=phone, erro=str(exc))
        return False

    if response.status_code != 200:
        log_erro("whatsapp_falhou", telefone=phone, status_http=response.status_code)
        return False

    log("whatsapp_enviado", telefone=phone)
    return True


async def request_otp(
    phone: str,
    session: AsyncSession,
    otp_sender: Callable[[str, str], Awaitable[bool]] = send_whatsapp_otp,
    code_generator: Callable[[], str] | None = None,
) -> dict:
    """Generate an OTP, persist it and attempt WhatsApp delivery."""
    authorized = await session.scalar(select(User).where(User.phone == phone))
    if not authorized:
        log("login_numero_nao_autorizado", telefone=phone)
        raise HTTPException(status_code=403, detail="Phone number not authorized")

    generator = code_generator or (lambda: str(random.randint(100000, 999999)))
    code = generator()
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    session.add(OTPCode(phone=phone, code=code, expires_at=expires_at))
    await session.commit()

    log("otp_gerado", telefone=phone)
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
        log("otp_invalido", telefone=phone)
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    if otp.expires_at < datetime.now(UTC):
        log("otp_expirado", telefone=phone)
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

    user_id = str(user.id)
    trips = await list_eligible_trips(user_id, session)
    identity = {
        "user_id": user_id,
        "phone": user.phone,
        "name": user.full_name,
    }
    log("login_ok", telefone=phone, usuario_id=user_id, viagens=len(trips))

    if user.role == "admin":
        return {
            **identity,
            "status": "admin_authenticated",
            "role": "admin",
            "message": "Login successful",
            "access_token": _create_admin_token(user_id, user.phone),
        }
    if not trips:
        return {
            **identity,
            "status": "no_trips",
            "message": "No current or future trips available",
        }
    if len(trips) == 1:
        return create_trip_session_payload(
            user_id, user.phone, user.full_name, trips[0], False
        )
    return {
        **identity,
        "status": "selection_required",
        "message": "Trip selection required",
        "selection_token": _create_selection_token(user_id, user.phone),
        "trips": trips,
    }

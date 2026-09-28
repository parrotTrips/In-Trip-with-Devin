"""Authentication HTTP routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import JWT_ALGORITHM, JWT_SECRET
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.auth import OTPRequest, OTPVerify, TripSelectionRequest
from app.services.auth_service import (
    create_trip_session_payload,
    request_otp,
    verify_otp,
)
from app.services.trip_membership_service import (
    get_eligible_trip_membership,
    list_eligible_trips,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _decode_trip_choice_identity(request: Request) -> dict[str, str]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = jwt.decode(
            auth_header[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Unauthorized") from exc

    user_id = payload.get("sub")
    phone = payload.get("phone")
    token_type = payload.get("token_type")
    if (
        not isinstance(user_id, str)
        or not user_id
        or not isinstance(phone, str)
        or not phone
        or token_type not in {"trip_selection", "session"}
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Unauthorized") from exc
    return {"user_id": user_id, "phone": phone}


@router.post("/request-otp")
async def request_otp_handler(
    req: OTPRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Generate and send an OTP for the requested phone number."""
    return await request_otp(req.phone, session)


@router.post("/verify-otp")
async def verify_otp_handler(
    req: OTPVerify,
    session: AsyncSession = Depends(get_db_session),
):
    """Validate an OTP and return the current user identity payload."""
    return await verify_otp(req.phone, req.code, session)


@router.get("/trips")
async def list_my_trips(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Refresh the current/future trips available to the authenticated person."""
    identity = _decode_trip_choice_identity(request)
    return {"trips": await list_eligible_trips(identity["user_id"], session)}


@router.post("/select-trip")
async def select_trip(
    req: TripSelectionRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Exchange a valid auth token for a trip-scoped session token."""
    identity = _decode_trip_choice_identity(request)
    membership = await get_eligible_trip_membership(
        identity["user_id"], req.trip_id, session
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Trip not available")
    user = await session.get(User, UUID(identity["user_id"]))
    return create_trip_session_payload(
        identity["user_id"],
        identity["phone"],
        user.full_name if user else None,
        membership,
    )

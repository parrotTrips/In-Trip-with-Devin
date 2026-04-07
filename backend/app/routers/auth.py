"""Authentication HTTP routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.auth import OTPRequest, OTPVerify
from app.services.auth_service import request_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["auth"])


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

"""Authentication HTTP routes."""

from fastapi import APIRouter

from app.schemas.auth import OTPRequest, OTPVerify
from app.services.auth_service import request_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-otp")
async def request_otp_handler(req: OTPRequest):
    """Generate and send an OTP for the requested phone number."""
    return await request_otp(req.phone)


@router.post("/verify-otp")
async def verify_otp_handler(req: OTPVerify):
    """Validate an OTP and return the current user identity payload."""
    return await verify_otp(req.phone, req.code)

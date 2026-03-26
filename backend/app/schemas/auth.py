"""Authentication request schemas."""

from pydantic import BaseModel


class OTPRequest(BaseModel):
    """Phone number used to request a login OTP."""

    phone: str


class OTPVerify(BaseModel):
    """Phone/code pair used to validate an OTP."""

    phone: str
    code: str

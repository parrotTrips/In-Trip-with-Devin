"""QR payload signing service functions."""

from __future__ import annotations

from jose import jwt

from app.core.config import JWT_ALGORITHM, JWT_SECRET

TRAVELER_QR_PAYLOAD_TYPE = "traveler_checkin"


def create_traveler_qr_payload(trip_traveler_id: str, trip_uuid: str) -> str:
    payload = {
        "type": TRAVELER_QR_PAYLOAD_TYPE,
        "trip_traveler_id": trip_traveler_id,
        "trip_uuid": trip_uuid,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_traveler_qr_payload(token: str) -> dict:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if payload.get("type") != TRAVELER_QR_PAYLOAD_TYPE:
        raise ValueError("Invalid QR payload type")
    return payload

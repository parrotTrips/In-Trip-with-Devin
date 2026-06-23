import pytest
from jose import JWTError, jwt

from app.core.config import JWT_ALGORITHM, JWT_SECRET
from app.services.qr_service import (
    create_traveler_qr_payload,
    decode_traveler_qr_payload,
)


def test_signed_traveler_qr_payload_can_be_decoded():
    token = create_traveler_qr_payload(
        trip_traveler_id="traveler-123",
        trip_uuid="trip-abc",
    )

    payload = decode_traveler_qr_payload(token)

    assert payload == {
        "type": "traveler_checkin",
        "trip_traveler_id": "traveler-123",
        "trip_uuid": "trip-abc",
    }


def test_tampered_traveler_qr_payload_is_rejected():
    token = create_traveler_qr_payload(
        trip_traveler_id="traveler-123",
        trip_uuid="trip-abc",
    )
    replacement = "a" if token[-1] != "a" else "b"
    tampered_token = f"{token[:-1]}{replacement}"

    with pytest.raises(JWTError):
        decode_traveler_qr_payload(tampered_token)


def test_wrong_traveler_qr_payload_type_is_rejected():
    token = jwt.encode(
        {
            "type": "staff_checkin",
            "trip_traveler_id": "traveler-123",
            "trip_uuid": "trip-abc",
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(ValueError, match="Invalid QR payload type"):
        decode_traveler_qr_payload(token)

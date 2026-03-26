import sys

from fastapi.testclient import TestClient


MODULES_TO_CLEAR = [
    "app.main",
    "app.routers.health",
    "app.routers.auth",
    "app.routers.users",
]


def build_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)

    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)

    from app.main import app

    return TestClient(app)


def test_request_otp_route_returns_debug_code(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        response = client.post("/auth/request-otp", json={"phone": "+5511666666666"})

    assert response.status_code == 200
    assert response.json()["message"] == (
        "OTP generated (WhatsApp delivery failed, showing code for testing)"
    )
    assert len(response.json()["debug_code"]) == 6


def test_verify_otp_route_creates_user_on_first_login(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        otp_response = client.post("/auth/request-otp", json={"phone": "+5511555555555"})
        verify_response = client.post(
            "/auth/verify-otp",
            json={
                "phone": "+5511555555555",
                "code": otp_response.json()["debug_code"],
            },
        )

    assert verify_response.status_code == 200
    assert verify_response.json() == {
        "user_id": 1,
        "phone": "+5511555555555",
        "name": None,
        "message": "Login successful",
    }

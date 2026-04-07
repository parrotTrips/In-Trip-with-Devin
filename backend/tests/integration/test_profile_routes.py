import sys

from fastapi.testclient import TestClient


MODULES_TO_CLEAR = [
    "app.main",
    "app.routers.health",
    "app.routers.auth",
    "app.routers.users",
    "app.routers.profile",
    "app.routers.checklist",
]


def build_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)

    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)

    from app.main import app

    return TestClient(app)


def create_user(client, phone="+5511990000000"):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    return verify_response.json()["user_id"]


def test_profile_routes_read_and_update_profile(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client)
        initial_response = client.get(f"/profile/{user_id}")
        update_response = client.put(
            f"/profile/{user_id}",
            json={"preferred_name": "Eva", "email": "eva@example.com"},
        )
        updated_response = client.get(f"/profile/{user_id}")

    assert initial_response.status_code == 200
    assert initial_response.json()["profile"] is None
    assert update_response.status_code == 200
    assert update_response.json() == {"message": "Profile updated"}
    assert updated_response.status_code == 200
    assert updated_response.json()["name"] == "Eva"
    assert updated_response.json()["profile"]["preferred_name"] == "Eva"
    assert updated_response.json()["profile"]["email"] == "eva@example.com"

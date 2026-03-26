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


def create_user(client, phone="+5511444444444"):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    return verify_response.json()["user_id"]


def test_get_user_route_returns_existing_user(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client)
        response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": user_id,
        "phone": "+5511444444444",
        "name": None,
    }


def test_update_user_route_preserves_contract(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client, phone="+5511333333333")
        update_response = client.put(f"/users/{user_id}", json={"name": "Carol"})
        get_response = client.get(f"/users/{user_id}")

    assert update_response.status_code == 200
    assert update_response.json() == {"message": "User updated"}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "id": user_id,
        "phone": "+5511333333333",
        "name": "Carol",
    }

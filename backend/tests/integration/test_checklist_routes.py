import sys

from fastapi.testclient import TestClient


MODULES_TO_CLEAR = [
    "app.main",
    "app.routers.health",
    "app.routers.auth",
    "app.routers.users",
    "app.routers.profile",
    "app.routers.checklist",
    "app.routers.comments",
]


def build_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)

    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)

    from app.main import app

    return TestClient(app)


def create_user(client, phone="+5511991000000"):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    return verify_response.json()["user_id"]


def test_checklist_routes_persist_progress(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client)
        update_response = client.post(
            f"/checklist/update?user_id={user_id}",
            json={
                "trip_id": "ross26",
                "phase_id": "phase-1",
                "item_id": "passport",
                "completed": True,
            },
        )
        get_response = client.get(f"/checklist/ross26/{user_id}")

    assert update_response.status_code == 200
    assert update_response.json() == {"message": "Checklist item updated"}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "trip_id": "ross26",
        "user_id": user_id,
        "progress": {"phase-1": {"passport": True}},
    }


def test_phase_routes_persist_completion(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client, phone="+5511991000001")
        update_response = client.post(
            f"/phases/complete?user_id={user_id}",
            json={"trip_id": "ross26", "phase_id": "phase-1", "completed": True},
        )
        get_response = client.get(f"/phases/ross26/{user_id}")

    assert update_response.status_code == 200
    assert update_response.json() == {"message": "Phase completion updated"}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "trip_id": "ross26",
        "user_id": user_id,
        "completions": {"phase-1": True},
    }

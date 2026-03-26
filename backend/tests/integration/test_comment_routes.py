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


def create_user(client, phone="+5511992000000"):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    return verify_response.json()["user_id"]


def test_comment_routes_persist_and_list_public_comments(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client)
        create_response = client.post(
            f"/comments?user_id={user_id}",
            json={
                "trip_id": "ross26",
                "phase_id": "phase-1",
                "text": "Visible comment",
                "is_private": False,
            },
        )
        list_response = client.get("/comments/ross26/phase-1")

    assert create_response.status_code == 200
    assert create_response.json() == {"message": "Comment added"}
    assert list_response.status_code == 200
    assert list_response.json()["trip_id"] == "ross26"
    assert list_response.json()["phase_id"] == "phase-1"
    assert len(list_response.json()["comments"]) == 1
    assert list_response.json()["comments"][0]["text"] == "Visible comment"
    assert list_response.json()["comments"][0]["is_private"] is False

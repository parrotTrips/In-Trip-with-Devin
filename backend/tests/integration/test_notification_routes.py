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
    "app.routers.notifications",
    "app.routers.missions",
]


def build_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)

    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)

    from app.main import app

    return TestClient(app)


def create_user(client, phone):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    return verify_response.json()["user_id"]


def test_notification_routes_read_and_mark_notifications(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client, "+5511660000000")
        create_response = client.post(
            "/notifications",
            json={
                "user_id": user_id,
                "trip_id": "ross26",
                "title": "Ping",
                "body": "Route contract",
                "type": "info",
                "link": "/missions",
            },
        )
        list_response = client.get(f"/notifications/{user_id}")
        count_response = client.get(f"/notifications/{user_id}/count")
        notification_id = list_response.json()["notifications"][0]["id"]
        mark_response = client.put(f"/notifications/{notification_id}/read")
        read_all_response = client.put(f"/notifications/{user_id}/read-all")
        final_count_response = client.get(f"/notifications/{user_id}/count")

    assert create_response.status_code == 200
    assert create_response.json() == {"message": "Notification created"}
    assert list_response.status_code == 200
    assert list_response.json()["unread_count"] == 1
    assert count_response.json() == {"unread_count": 1}
    assert mark_response.json() == {"message": "Notification marked as read"}
    assert read_all_response.json() == {"message": "All notifications marked as read"}
    assert final_count_response.json() == {"unread_count": 0}


def test_notification_routes_broadcast_to_all_users(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        first_user_id = create_user(client, "+5511660000001")
        second_user_id = create_user(client, "+5511660000002")
        broadcast_response = client.post(
            "/notifications/broadcast?title=Broadcast&body=Everyone"
        )
        first_list_response = client.get(f"/notifications/{first_user_id}")
        second_list_response = client.get(f"/notifications/{second_user_id}")

    assert broadcast_response.status_code == 200
    assert broadcast_response.json() == {"message": "Notification sent to 2 users"}
    assert first_list_response.json()["unread_count"] == 1
    assert second_list_response.json()["unread_count"] == 1

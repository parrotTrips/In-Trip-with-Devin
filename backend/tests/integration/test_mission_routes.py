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


def test_mission_routes_read_complete_and_uncomplete(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client, "+5511550000000")
        missions_response = client.get(f"/missions/ross26?user_id={user_id}")
        mission_id = missions_response.json()["missions"][0]["id"]
        complete_response = client.post(
            f"/missions/ross26/complete?user_id={user_id}",
            json={"mission_id": mission_id},
        )
        completed_response = client.get(f"/missions/ross26?user_id={user_id}")
        uncomplete_response = client.request(
            "DELETE",
            f"/missions/ross26/uncomplete?user_id={user_id}",
            json={"mission_id": mission_id},
        )

    assert missions_response.status_code == 200
    assert len(missions_response.json()["missions"]) == 12
    assert complete_response.status_code == 200
    assert complete_response.json()["already_completed"] is False
    assert completed_response.json()["missions"][0]["completed"] is True
    assert uncomplete_response.json() == {"message": "Mission uncompleted"}


def test_mission_routes_report_leaderboard_and_points(monkeypatch, tmp_path):
    with build_client(monkeypatch, tmp_path) as client:
        user_id = create_user(client, "+5511550000001")
        missions_response = client.get(f"/missions/ross26?user_id={user_id}")
        mission_id = missions_response.json()["missions"][0]["id"]
        client.post(
            f"/missions/ross26/complete?user_id={user_id}",
            json={"mission_id": mission_id},
        )
        leaderboard_response = client.get("/missions/ross26/leaderboard")
        points_response = client.get(f"/missions/ross26/user/{user_id}/points")

    assert leaderboard_response.status_code == 200
    assert leaderboard_response.json()["leaderboard"][0]["user_id"] == user_id
    assert points_response.status_code == 200
    assert points_response.json()["user_id"] == user_id
    assert points_response.json()["missions_completed"] == 1
    assert points_response.json()["total_points"] > 0

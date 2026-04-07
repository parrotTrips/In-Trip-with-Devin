def create_user(client, phone="+5511444444444"):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    return verify_response.json()["user_id"]


def test_get_user_route_returns_existing_user(client):
    user_id = create_user(client)
    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": user_id,
        "phone": "+5511444444444",
        "name": None,
    }


def test_update_user_route_preserves_contract(client):
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

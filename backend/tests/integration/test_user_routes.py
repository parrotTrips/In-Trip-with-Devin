def create_user(client, phone="+5511444444444"):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    data = verify_response.json()
    return data["user_id"], data["access_token"]


def test_get_user_route_returns_existing_user(client):
    user_id, token = create_user(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/users/{user_id}", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": user_id,
        "phone": "+5511444444444",
        "name": None,
    }


def test_update_user_route_preserves_contract(client):
    user_id, token = create_user(client, phone="+5511333333333")
    headers = {"Authorization": f"Bearer {token}"}
    update_response = client.put(f"/users/{user_id}", json={"name": "Carol"}, headers=headers)
    get_response = client.get(f"/users/{user_id}", headers=headers)

    assert update_response.status_code == 200
    assert update_response.json() == {"message": "User updated"}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "id": user_id,
        "phone": "+5511333333333",
        "name": "Carol",
    }

from uuid import UUID


def test_request_otp_route_returns_debug_code(seeded_client):
    response = seeded_client.post("/auth/request-otp", json={"phone": "+5511666666666"})

    assert response.status_code == 200
    assert response.json()["message"] == (
        "OTP generated (WhatsApp delivery failed, showing code for testing)"
    )
    assert len(response.json()["debug_code"]) == 6


def test_verify_otp_route_creates_user_on_first_login(seeded_client):
    otp_response = seeded_client.post("/auth/request-otp", json={"phone": "+5511555555555"})
    verify_response = seeded_client.post(
        "/auth/verify-otp",
        json={
            "phone": "+5511555555555",
            "code": otp_response.json()["debug_code"],
        },
    )

    assert verify_response.status_code == 200
    assert verify_response.json()["phone"] == "+5511555555555"
    assert verify_response.json()["name"] is None
    assert verify_response.json()["message"] == "Login successful"
    assert UUID(verify_response.json()["user_id"])
    assert verify_response.json()["access_token"]

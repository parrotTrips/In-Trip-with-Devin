"""Integration tests for JWT authentication middleware."""

from datetime import UTC, datetime, timedelta

from jose import jwt


TEST_SECRET = "test-secret-for-middleware"
TEST_ALGORITHM = "HS256"


def _make_token(user_id: str = "abc-123", phone: str = "+5511999999999", days: int = 14) -> str:
    expire = datetime.now(UTC) + timedelta(days=days)
    return jwt.encode(
        {"sub": user_id, "phone": phone, "exp": expire},
        TEST_SECRET,
        algorithm=TEST_ALGORITHM,
    )


def _make_expired_token() -> str:
    expire = datetime.now(UTC) - timedelta(seconds=1)
    return jwt.encode(
        {"sub": "abc-123", "phone": "+5511999999999", "exp": expire},
        TEST_SECRET,
        algorithm=TEST_ALGORITHM,
    )


def _make_qr_like_token(secret: str) -> str:
    return jwt.encode(
        {
            "type": "traveler_checkin",
            "trip_traveler_id": "traveler-123",
            "trip_uuid": "trip-abc",
        },
        secret,
        algorithm=TEST_ALGORITHM,
    )


def test_healthz_is_public(seeded_client):
    response = seeded_client.get("/healthz")
    assert response.status_code == 200


def test_auth_routes_are_public(seeded_client):
    response = seeded_client.post("/auth/request-otp", json={"phone": "+5511111111111"})
    assert response.status_code == 200


def test_protected_route_without_token_returns_401(seeded_client):
    otp_resp = seeded_client.post("/auth/request-otp", json={"phone": "+5511222222222"})
    code = otp_resp.json()["debug_code"]
    verify_resp = seeded_client.post(
        "/auth/verify-otp", json={"phone": "+5511222222222", "code": code}
    )
    user_id = verify_resp.json()["user_id"]

    response = seeded_client.get(f"/profile/{user_id}", params={"trip_id": "test-trip"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_protected_route_with_valid_token_passes(seeded_client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)

    otp_resp = seeded_client.post("/auth/request-otp", json={"phone": "+5511333333333"})
    code = otp_resp.json()["debug_code"]
    verify_resp = seeded_client.post(
        "/auth/verify-otp", json={"phone": "+5511333333333", "code": code}
    )
    token = verify_resp.json()["access_token"]
    user_id = verify_resp.json()["user_id"]

    response = seeded_client.get(
        f"/profile/{user_id}",
        params={"trip_id": "test-trip"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code != 401


def test_protected_route_with_expired_token_returns_401(seeded_client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    expired_token = _make_expired_token()

    otp_resp = seeded_client.post("/auth/request-otp", json={"phone": "+5511444444444"})
    code = otp_resp.json()["debug_code"]
    verify_resp = seeded_client.post(
        "/auth/verify-otp", json={"phone": "+5511444444444", "code": code}
    )
    user_id = verify_resp.json()["user_id"]

    response = seeded_client.get(
        f"/profile/{user_id}",
        params={"trip_id": "test-trip"},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_protected_route_with_invalid_token_returns_401(seeded_client):
    otp_resp = seeded_client.post("/auth/request-otp", json={"phone": "+5511555444333"})
    code = otp_resp.json()["debug_code"]
    verify_resp = seeded_client.post(
        "/auth/verify-otp", json={"phone": "+5511555444333", "code": code}
    )
    user_id = verify_resp.json()["user_id"]

    response = seeded_client.get(
        f"/profile/{user_id}",
        params={"trip_id": "test-trip"},
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_protected_route_with_signed_non_auth_payload_returns_401(seeded_client):
    from app.core.config import JWT_SECRET

    token = _make_qr_like_token(JWT_SECRET)
    otp_resp = seeded_client.post("/auth/request-otp", json={"phone": "+5511991000000"})
    code = otp_resp.json()["debug_code"]
    verify_resp = seeded_client.post(
        "/auth/verify-otp", json={"phone": "+5511991000000", "code": code}
    )
    user_id = verify_resp.json()["user_id"]

    response = seeded_client.get(
        f"/profile/{user_id}",
        params={"trip_id": "test-trip"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

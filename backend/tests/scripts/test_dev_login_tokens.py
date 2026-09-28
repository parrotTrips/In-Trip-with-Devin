"""The dev-login helper scripts (gen_dev_users.py, seed_marcelo_test_user.py) must
mint real trip-scoped session tokens (token_type="session", trip_id, role) — the
JWTAuthMiddleware rejects any token missing those claims, which is exactly what
broke VITE_DEV_TOKEN dev auto-login and DevUserSwitcher after multi-trip login
shipped. These tests only exercise the token-building helpers directly (no DB).
"""

import sys
from pathlib import Path

from jose import jwt

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

TEST_SECRET = "test-secret-for-dev-tokens"


def test_gen_dev_users_creates_session_token_with_trip_and_role(monkeypatch):
    from scripts.gen_dev_users import _create_jwt

    monkeypatch.setattr("app.services.auth_service.JWT_SECRET", TEST_SECRET)

    token = _create_jwt("user-123", "+5511999990000", "trip-abc", "traveler")
    claims = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    assert claims["token_type"] == "session"
    assert claims["trip_id"] == "trip-abc"
    assert claims["role"] == "traveler"
    assert claims["sub"] == "user-123"
    assert claims["phone"] == "+5511999990000"


def test_seed_marcelo_test_user_creates_session_token_with_trip_and_role(monkeypatch):
    from scripts.seed_marcelo_test_user import TRIP_UUID, _create_jwt

    monkeypatch.setattr("app.services.auth_service.JWT_SECRET", TEST_SECRET)

    token = _create_jwt("user-456", "+5511999990001")
    claims = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    assert claims["token_type"] == "session"
    assert claims["trip_id"] == TRIP_UUID
    assert claims["role"] == "traveler"
    assert claims["sub"] == "user-456"

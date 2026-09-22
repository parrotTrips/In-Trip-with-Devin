import asyncio

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


VALID_CLAIMS = {
    "sub": "google-user-123",
    "email": "pessoa@parrottrips.com",
    "email_verified": True,
    "hd": "parrottrips.com",
}


@pytest.fixture(autouse=True)
def configured_auth(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "false")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client.apps.googleusercontent.com")
    monkeypatch.setenv("ALLOWED_EMAIL_DOMAIN", "parrottrips.com")


def credentials(token: str = "google-token") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def authenticate(auth_module, token: HTTPAuthorizationCredentials | None = None):
    return asyncio.run(auth_module.require_console_access(token))


def test_missing_bearer_returns_401():
    from app.core import console_auth

    with pytest.raises(HTTPException) as exc:
        authenticate(console_auth)
    assert exc.value.status_code == 401


def test_missing_server_configuration_returns_503(monkeypatch):
    from app.core import console_auth

    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID")
    with pytest.raises(HTTPException) as exc:
        authenticate(console_auth, credentials())
    assert exc.value.status_code == 503


def test_valid_workspace_claims_return_principal(monkeypatch):
    from app.core import console_auth

    monkeypatch.setattr(console_auth, "_verify_google_token_sync", lambda *_: VALID_CLAIMS)
    principal = authenticate(console_auth, credentials())
    assert principal.uid == "google-user-123"
    assert principal.email == "pessoa@parrottrips.com"


def test_invalid_google_token_returns_401(monkeypatch):
    from app.core import console_auth

    def invalid(*_):
        raise ValueError("invalid token")

    monkeypatch.setattr(console_auth, "_verify_google_token_sync", invalid)
    with pytest.raises(HTTPException) as exc:
        authenticate(console_auth, credentials())
    assert exc.value.status_code == 401
    assert exc.value.detail == "Unauthorized"


@pytest.mark.parametrize(
    "claims",
    [
        {**VALID_CLAIMS, "email_verified": False},
        {**VALID_CLAIMS, "email": "pessoa@example.com"},
        {key: value for key, value in VALID_CLAIMS.items() if key != "hd"},
        {**VALID_CLAIMS, "hd": "example.com"},
        {key: value for key, value in VALID_CLAIMS.items() if key != "sub"},
        {**VALID_CLAIMS, "sub": ""},
    ],
)
def test_invalid_workspace_claims_return_403(monkeypatch, claims):
    from app.core import console_auth

    monkeypatch.setattr(console_auth, "_verify_google_token_sync", lambda *_: claims)
    with pytest.raises(HTTPException) as exc:
        authenticate(console_auth, credentials())
    assert exc.value.status_code == 403


def test_local_bypass_requires_development_and_flag(monkeypatch):
    from app.core import console_auth

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "true")
    principal = authenticate(console_auth)
    assert principal.uid == "local-console"


@pytest.mark.parametrize(
    ("app_env", "enabled"),
    [("production", "true"), ("development", "false")],
)
def test_local_bypass_stays_closed_without_both_guards(monkeypatch, app_env, enabled):
    from app.core import console_auth

    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", enabled)
    with pytest.raises(HTTPException) as exc:
        authenticate(console_auth)
    assert exc.value.status_code == 401


def test_raw_token_is_absent_from_logs_and_error(monkeypatch):
    from app.core import console_auth

    raw_token = "secret-google-token-sentinel"
    logged: list[tuple[tuple, dict]] = []

    def unexpected(*_):
        raise RuntimeError(f"network failed while checking {raw_token}")

    monkeypatch.setattr(console_auth, "_verify_google_token_sync", unexpected)
    monkeypatch.setattr(console_auth, "log_erro", lambda *args, **kwargs: logged.append((args, kwargs)))

    with pytest.raises(HTTPException) as exc:
        authenticate(console_auth, credentials(raw_token))

    assert exc.value.status_code == 500
    assert raw_token not in str(exc.value.detail)
    assert raw_token not in repr(logged)

import importlib

from fastapi.testclient import TestClient


def test_health_remains_public(client, monkeypatch):
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "false")
    assert client.get("/health").status_code == 200


def test_docs_are_available_in_development(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_docs_are_disabled_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    import app.main as main

    production_app = importlib.reload(main).app
    with TestClient(production_app) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_allowed_origin_receives_cors_on_authentication_error(client, monkeypatch):
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "false")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client.apps.googleusercontent.com")
    response = client.get(
        "/console/trips", headers={"Origin": "http://localhost:5174"}
    )
    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_disallowed_origin_does_not_receive_cors(client):
    response = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_allowed_preflight_accepts_authorization_header(client):
    response = client.options(
        "/console/trips",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"

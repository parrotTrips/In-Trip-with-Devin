import asyncio
import importlib
import sqlite3
import sys
from pathlib import Path


def load_config_module(monkeypatch, **env_overrides):
    """Reload the config module with explicit environment overrides."""
    for key in (
        "WHATSAPP_PHONE_NUMBER_ID",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_TEMPLATE_NAME",
        "DATABASE_PATH",
    ):
        monkeypatch.delenv(key, raising=False)

    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)

    sys.modules.pop("app.core.config", None)
    return importlib.import_module("app.core.config")


def test_config_uses_default_values(monkeypatch):
    config = load_config_module(monkeypatch)
    expected_database_path = Path(config.__file__).resolve().parents[2] / "app.db"

    assert config.WHATSAPP_PHONE_NUMBER_ID == ""
    assert config.WHATSAPP_ACCESS_TOKEN == ""
    assert config.WHATSAPP_TEMPLATE_NAME == "intripauth"
    assert config.DATABASE_PATH == str(expected_database_path)
    assert config.WHATSAPP_API_URL.endswith("/messages")


def test_init_db_creates_tables_for_the_active_scope(tmp_path):
    from app.db.database import init_db

    database_path = tmp_path / "test.db"

    asyncio.run(init_db(database_path))

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    expected_tables = {
        "users",
        "checklist_progress",
        "phase_completion",
        "comments",
        "otp_codes",
        "notifications",
        "user_profiles",
    }

    assert expected_tables.issubset(tables)


def test_init_db_uses_configured_database_path(monkeypatch, tmp_path):
    database_path = tmp_path / "configured.db"
    config = load_config_module(monkeypatch, DATABASE_PATH=str(database_path))
    database_module = importlib.import_module("app.db.database")

    asyncio.run(database_module.init_db())

    assert config.DATABASE_PATH == str(database_path)
    assert Path(database_path).exists()

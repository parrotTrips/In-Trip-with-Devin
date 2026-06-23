import asyncio
import contextlib
import importlib
import inspect
import os
import pytest
import shutil
import socket
import subprocess
import sys
import types
from pathlib import Path

import asyncpg
from alembic import command
from alembic.config import Config


def reload_module(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def load_config_module(monkeypatch, **env_overrides):
    defaults = {
        "WHATSAPP_PHONE_NUMBER_ID": "",
        "WHATSAPP_ACCESS_TOKEN": "",
        "WHATSAPP_TEMPLATE_NAME": "intripauth",
        "DATABASE_URL": "",
    }
    for key, value in defaults.items():
        monkeypatch.setenv(key, value)

    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)

    return reload_module("app.core.config")


def test_config_reads_database_url_from_environment(monkeypatch):
    config = load_config_module(
        monkeypatch,
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/parrot",
    )

    assert config.WHATSAPP_PHONE_NUMBER_ID == ""
    assert config.WHATSAPP_ACCESS_TOKEN == ""
    assert config.WHATSAPP_TEMPLATE_NAME == "intripauth"
    assert (
        config.DATABASE_URL
        == "postgresql+asyncpg://postgres:postgres@localhost:5432/parrot"
    )
    assert config.WHATSAPP_API_URL.endswith("/messages")


def test_app_startup_no_longer_calls_table_creation_helper(monkeypatch):
    main = reload_module("app.main")

    async def run_lifespan():
        async with main.lifespan(main.app):
            pass

    asyncio.run(run_lifespan())


def test_session_module_exposes_async_engine_and_session_factory():
    session_module = reload_module("app.db.session")

    assert session_module.engine is not None
    assert session_module.SessionLocal is not None
    assert inspect.isasyncgenfunction(session_module.get_db_session)
    assert inspect.iscoroutinefunction(session_module.dispose_engine)


def test_metadata_exposes_the_approved_postgres_tables():
    reload_module("app.db.models")
    base_module = importlib.import_module("app.db.base")

    expected_tables = {
        "users",
        "trip_travelers",
        "traveler_profiles",
        "trip_phases",
        "trip_phase_checklist_items",
        "trip_phase_links",
        "trip_activities",
        "traveler_checklist_progress",
        "traveler_phase_progress",
        "otp_codes",
        "trip_staff",
        "staff_tasks",
        "activity_checkins",
    }

    assert expected_tables.issubset(base_module.metadata.tables)


def test_staff_tasks_has_trip_activity_id_foreign_key():
    reload_module("app.db.models")
    base_module = importlib.import_module("app.db.base")

    staff_tasks = base_module.metadata.tables["staff_tasks"]

    assert "trip_activity_id" in staff_tasks.c
    fk_targets = {
        fk.column.table.name + "." + fk.column.name
        for fk in staff_tasks.c.trip_activity_id.foreign_keys
    }
    assert "trip_activities.id" in fk_targets


def test_activity_checkins_table_metadata():
    reload_module("app.db.models")
    base_module = importlib.import_module("app.db.base")

    activity_checkins = base_module.metadata.tables["activity_checkins"]

    fk_targets = {
        column.name: {
            fk.column.table.name + "." + fk.column.name
            for fk in column.foreign_keys
        }
        for column in activity_checkins.c
    }
    assert fk_targets["trip_activity_id"] == {"trip_activities.id"}
    assert fk_targets["trip_traveler_id"] == {"trip_travelers.id"}
    assert fk_targets["scanned_by_user_id"] == {"users.id"}

    unique_constraints = {
        tuple(column.name for column in constraint.columns)
        for constraint in activity_checkins.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("trip_activity_id", "trip_traveler_id") in unique_constraints


def test_alembic_database_url_defaults_to_application_config(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/from-env",
    )
    helper_module = reload_module("app.db.alembic_config")
    alembic_config = Config("alembic.ini")

    assert (
        helper_module.get_alembic_database_url(alembic_config)
        == "postgresql+asyncpg://postgres:postgres@localhost:5432/from-env"
    )


def test_alembic_database_url_allows_explicit_override(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/from-env",
    )
    helper_module = reload_module("app.db.alembic_config")
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option(
        "sqlalchemy.url",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/override",
    )

    assert (
        helper_module.get_alembic_database_url(alembic_config)
        == "postgresql+asyncpg://postgres:postgres@localhost:5432/override"
    )


def _find_free_port() -> int:
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
    except PermissionError as exc:
        pytest.skip(f"Environment does not allow binding a local PostgreSQL port: {exc}")


def _find_postgres_executable(name: str) -> Path | None:
    postgres_bin_dir = os.environ.get("POSTGRES_BIN_DIR")
    if postgres_bin_dir:
        candidate = Path(postgres_bin_dir) / name
        if candidate.exists():
            return candidate

    resolved = shutil.which(name)
    if resolved:
        return Path(resolved)

    return None


def _run_command(*args: str) -> None:
    subprocess.run(args, check=True, capture_output=True, text=True)


@contextlib.contextmanager
def temporary_postgres_database(tmp_path):
    initdb = _find_postgres_executable("initdb")
    pg_ctl = _find_postgres_executable("pg_ctl")
    createdb = _find_postgres_executable("createdb")
    if not initdb or not pg_ctl or not createdb:
        pytest.skip(
            "PostgreSQL binaries not available in PATH or POSTGRES_BIN_DIR"
        )

    data_dir = tmp_path / "pgdata"
    log_file = tmp_path / "postgres.log"
    port = _find_free_port()

    _run_command(
        str(initdb),
        "-D",
        str(data_dir),
        "-U",
        "postgres",
        "-A",
        "trust",
    )
    _run_command(
        str(pg_ctl),
        "-D",
        str(data_dir),
        "-l",
        str(log_file),
        "-o",
        f"-F -p {port}",
        "start",
        "-w",
    )

    try:
        _run_command(
            str(createdb),
            "-h",
            "127.0.0.1",
            "-p",
            str(port),
            "-U",
            "postgres",
            "parrot_trips_test",
        )
        yield f"postgresql+asyncpg://postgres@127.0.0.1:{port}/parrot_trips_test"
    finally:
        _run_command(
            str(pg_ctl),
            "-D",
            str(data_dir),
            "stop",
            "-m",
            "immediate",
        )


def test_alembic_upgrade_creates_the_full_schema(monkeypatch, tmp_path):
    expected_tables = {
        "users",
        "trip_travelers",
        "traveler_profiles",
        "trip_phases",
        "trip_phase_checklist_items",
        "trip_phase_links",
        "trip_activities",
        "media_assets",
        "activity_media",
        "traveler_checklist_progress",
        "traveler_phase_progress",
        "otp_codes",
        "trip_staff",
        "staff_tasks",
        "activity_checkins",
    }

    with temporary_postgres_database(tmp_path) as database_url:
        monkeypatch.setenv("DATABASE_URL", database_url)
        alembic_config = Config("alembic.ini")

        command.upgrade(alembic_config, "head")

        async def fetch_tables():
            connection = await asyncpg.connect(
                database_url.replace("postgresql+asyncpg://", "postgresql://")
            )
            try:
                rows = await connection.fetch(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    """
                )
            finally:
                await connection.close()

            return {row["tablename"] for row in rows}

        tables = asyncio.run(fetch_tables())

    assert expected_tables.issubset(tables)


def test_active_backend_files_do_not_reference_sqlite_runtime():
    files_to_check = [
        Path("app"),
        Path("tests"),
        Path(".env.example"),
        Path("README.md"),
    ]
    forbidden_patterns = (
        "aio" "sqlite",
        "DATABASE" "_PATH",
        "init_" "db(",
    )

    matches: list[str] = []
    for target in files_to_check:
        if target.is_dir():
            for path in target.rglob("*"):
                if not path.is_file():
                    continue
                if "__pycache__" in path.parts or path.suffix == ".pyc":
                    continue
                content = path.read_text(encoding="utf-8")
                for pattern in forbidden_patterns:
                    if pattern in content:
                        matches.append(f"{path}:{pattern}")
        else:
            content = target.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                if pattern in content:
                    matches.append(f"{target}:{pattern}")

    assert matches == []

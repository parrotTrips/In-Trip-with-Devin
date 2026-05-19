import asyncio
import contextlib
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

MODULES_TO_CLEAR = [
    "app.main",
    "app.core.config",
    "app.db.session",
    "app.services.auth_service",
    "app.services.user_service",
    "app.services.profile_service",
    "app.services.checklist_service",
    "app.routers.health",
    "app.routers.auth",
    "app.routers.users",
    "app.routers.profile",
    "app.routers.checklist",
    "app.middleware.auth",
]


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
        pytest.skip("PostgreSQL binaries not available in PATH or POSTGRES_BIN_DIR")

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


@pytest.fixture
def database_url(tmp_path):
    with temporary_postgres_database(tmp_path) as database_url:
        alembic_config = Config("alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(alembic_config, "head")
        yield database_url


@pytest.fixture
def session_factory(database_url):
    engine = create_async_engine(database_url, future=True, poolclass=pool.NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    asyncio.run(engine.dispose())


@pytest.fixture
def client(monkeypatch, database_url):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-for-testing-only")
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)

    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

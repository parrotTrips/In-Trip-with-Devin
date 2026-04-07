"""Helpers for aligning Alembic with the application database configuration."""

from __future__ import annotations

from alembic.config import Config

from app.core.config import get_database_url


def get_alembic_database_url(config: Config) -> str:
    configured_url = config.get_main_option("sqlalchemy.url")
    if configured_url:
        return configured_url

    return get_database_url()


def get_alembic_section(config: Config) -> dict[str, str]:
    section = dict(config.get_section(config.config_ini_section, {}) or {})
    section["sqlalchemy.url"] = get_alembic_database_url(config)
    return section

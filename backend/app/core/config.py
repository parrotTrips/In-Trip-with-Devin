"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_WHATSAPP_TEMPLATE_NAME = "intripauth"
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/parrot_trips"
)

WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_TEMPLATE_NAME = os.environ.get(
    "WHATSAPP_TEMPLATE_NAME", DEFAULT_WHATSAPP_TEMPLATE_NAME
)
WHATSAPP_TEMPLATE_LANGUAGE = os.environ.get("WHATSAPP_TEMPLATE_LANGUAGE", "pt_BR")
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
WHATSAPP_API_URL = (
    f"https://graph.facebook.com/v25.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
)

JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 14


def get_database_url() -> str:
    """Return the configured SQLAlchemy database URL."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

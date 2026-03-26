"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_WHATSAPP_TEMPLATE_NAME = "intripauth"
DEFAULT_DATABASE_PATH = "/data/app.db"

WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_TEMPLATE_NAME = os.environ.get(
    "WHATSAPP_TEMPLATE_NAME", DEFAULT_WHATSAPP_TEMPLATE_NAME
)
DATABASE_PATH = os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)
WHATSAPP_API_URL = (
    f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
)


def get_database_path() -> str:
    """Return the configured SQLite path, honoring runtime env overrides."""
    return os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)

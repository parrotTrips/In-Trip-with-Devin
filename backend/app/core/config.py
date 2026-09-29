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
    f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
)

JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 14
JWT_SELECTION_EXPIRY_MINUTES = int(
    os.environ.get("JWT_SELECTION_EXPIRY_MINUTES", "15")
)


def get_database_url() -> str:
    """Return the configured SQLAlchemy database URL."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_app_env() -> str:
    """Return the normalized runtime environment name."""
    return os.environ.get("APP_ENV", "development").strip().lower()


def console_local_bypass_enabled() -> bool:
    """Allow local console access only behind both development guards."""
    return (
        get_app_env() == "development"
        and os.environ.get("ENABLE_CONSOLE_LOCAL", "false").strip().lower() == "true"
    )


def get_google_oauth_client_id() -> str:
    return os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()


def get_allowed_email_domain() -> str:
    return os.environ.get("ALLOWED_EMAIL_DOMAIN", "").strip().lower()


def get_cors_allowed_origins() -> list[str]:
    raw = os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,https://parrot-trips.netlify.app",
    )
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]

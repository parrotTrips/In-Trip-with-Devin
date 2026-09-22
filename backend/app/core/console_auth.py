"""Google Workspace authentication for the content console."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import cachecontrol
import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app.core.config import (
    console_local_bypass_enabled,
    get_allowed_email_domain,
    get_google_oauth_client_id,
)
from app.core.logger import log_erro

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    uid: str
    email: str


class _TimeoutRequest(Request):
    """Google transport with a bounded network wait."""

    def __call__(self, *args, timeout=10, **kwargs):
        return super().__call__(*args, timeout=timeout, **kwargs)


@lru_cache(maxsize=1)
def _google_request() -> Request:
    session = cachecontrol.CacheControl(requests.Session())
    return _TimeoutRequest(session=session)


def _verify_google_token_sync(token: str, audience: str) -> dict:
    return id_token.verify_oauth2_token(
        token,
        _google_request(),
        audience=audience,
        clock_skew_in_seconds=10,
    )


def _validate_workspace_claims(claims: dict, domain: str) -> AuthenticatedPrincipal:
    email = claims.get("email")
    sub = claims.get("sub")
    email_domain = email.lower().rsplit("@", 1)[-1] if isinstance(email, str) else None
    if (
        claims.get("email_verified") is not True
        or email_domain != domain
        or claims.get("hd") != domain
        or not isinstance(sub, str)
        or not sub.strip()
    ):
        raise HTTPException(status_code=403, detail="Google Workspace account not authorized")
    return AuthenticatedPrincipal(uid=sub, email=email.lower())


async def require_console_access(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> AuthenticatedPrincipal:
    """Authenticate one console request without creating a backend session."""
    if console_local_bypass_enabled():
        return AuthenticatedPrincipal(uid="local-console", email="local@parrottrips.com")

    audience = get_google_oauth_client_id()
    domain = get_allowed_email_domain()
    if not audience or not domain:
        raise HTTPException(status_code=503, detail="Console authentication is not configured")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        claims = await asyncio.to_thread(
            _verify_google_token_sync, credentials.credentials, audience
        )
    except (ValueError, google_auth_exceptions.GoogleAuthError):
        raise HTTPException(status_code=401, detail="Unauthorized") from None
    except Exception as exc:
        log_erro("console_google_auth_failure", error_type=type(exc).__name__)
        raise HTTPException(status_code=500, detail="Unable to validate authentication") from None
    return _validate_workspace_claims(claims, domain)

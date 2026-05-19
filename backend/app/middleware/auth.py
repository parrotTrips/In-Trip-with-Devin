"""JWT authentication middleware."""

from __future__ import annotations

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import JWT_ALGORITHM, JWT_SECRET

_PUBLIC_PATHS = {"/healthz"}
_PUBLIC_PREFIXES = ("/auth",)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        token = auth_header[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.state.user_id = payload["sub"]
            request.state.phone = payload["phone"]
        except JWTError:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        return await call_next(request)

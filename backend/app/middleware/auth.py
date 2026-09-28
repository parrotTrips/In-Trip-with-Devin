"""JWT authentication middleware."""

from __future__ import annotations

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import JWT_ALGORITHM, JWT_SECRET
from app.core.logger import log

_PUBLIC_PATHS = {"/health", "/healthz"}
_PUBLIC_PREFIXES = ("/auth", "/admin")


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            log("jwt_ausente", rota=path)
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        token = auth_header[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            phone = payload.get("phone")
            if not user_id or not phone:
                log("jwt_payload_invalido", rota=path)
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
            token_type = payload.get("token_type")
            role = payload.get("role")
            trip_id = payload.get("trip_id")

            if token_type == "admin":
                if not path.startswith("/console") or role != "admin":
                    return JSONResponse({"detail": "Unauthorized"}, status_code=401)
            elif token_type == "session":
                if path.startswith("/console") or role not in {"traveler", "staff"} or not trip_id:
                    return JSONResponse({"detail": "Unauthorized"}, status_code=401)
            else:
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)

            request.state.user_id = user_id
            request.state.phone = phone
            request.state.role = role
            if token_type == "session":
                request.state.trip_id = trip_id
        except JWTError:
            log("jwt_invalido_ou_expirado", rota=path)
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        return await call_next(request)

# JWT Authentication Design

## Context

The app currently authenticates users via WhatsApp OTP (Meta Business API). After a successful OTP verification, the backend returns `{ user_id, phone, name }` and the frontend stores this in localStorage. There is no session token — the `user_id` is sent as a URL parameter and the backend trusts it blindly. Any request with a known `user_id` can read or modify another user's data including passport and payment information.

This spec defines the addition of JWT-based session management to the existing WhatsApp OTP flow, closing the security gap without changing the user experience.

## Requirements

- JWT issued on successful OTP verification, valid for 14 days (covering a full trip cycle).
- No refresh token — when the token expires the user logs in again via WhatsApp OTP.
- Token stored in localStorage alongside existing user data.
- All endpoints except `/auth/*` and `/healthz` require a valid JWT.
- A single middleware handles validation — no changes to individual route handlers.
- Frontend sends the token automatically on every API call — no changes to individual screens or services.

## Architecture

### Approach

Global HTTP middleware on the FastAPI backend intercepts all requests before they reach route handlers. Routes prefixed with `/auth` and `/healthz` are excluded. All others require a valid `Authorization: Bearer <token>` header. The frontend API client reads the token from localStorage and injects the header on every request.

### Components

**Backend — `app/core/config.py`**
- Add `JWT_SECRET` read from `.env` (required, no default).
- Add `JWT_ALGORITHM = "HS256"`.
- Add `JWT_EXPIRY_DAYS = 14`.

**Backend — `app/services/auth_service.py`**
- In `verify_otp`, after the user is created or retrieved, generate a signed JWT using `python-jose`.
- JWT payload: `{ "sub": str(user.id), "phone": user.phone, "exp": now + 14 days }`.
- Return `access_token` alongside existing fields `user_id`, `phone`, `name`.

**Backend — `app/middleware/auth.py`** (new file)
- `JWTAuthMiddleware(BaseHTTPMiddleware)` reads the `Authorization` header.
- Public paths: any path starting with `/auth` or equal to `/healthz`. Requests to these paths pass through unconditionally.
- For all other paths: decode and verify the JWT using `JWT_SECRET`. On success, attach `user_id` and `phone` to `request.state` for downstream use. On failure (missing, expired, invalid), return HTTP 401 with `{ "detail": "Unauthorized" }`.

**Backend — `app/main.py`**
- Register `JWTAuthMiddleware` with `app.add_middleware(JWTAuthMiddleware)`.

**Frontend — `src/app/providers/auth-context.ts`**
- Add `token: string` field to `AuthUser` interface.
- Add `token` parameter to the `login` function signature.

**Frontend — `src/app/providers/AuthProvider.tsx`**
- Pass `token` through to the `AuthContext` login call and persist it in localStorage as part of the `parrot_user` object.

**Frontend — `src/shared/api/client.ts`**
- Read `parrot_user` from localStorage and extract `token`.
- Include `Authorization: Bearer <token>` header in every `request()` call when a token is present.

**Frontend — `src/features/auth/services/auth-api.ts`**
- Update `verifyOTP` return type to include `access_token: string`.

**Frontend — `src/features/auth/pages/LoginScreen.tsx`**
- Pass `access_token` from the verify response to the `login(...)` call.

## Data Flow

```
User enters phone
      ↓
POST /auth/request-otp  →  OTP saved, WhatsApp sent
      ↓
User enters code
      ↓
POST /auth/verify-otp   →  OTP validated, JWT generated (14 days)
      ↓
Frontend stores { userId, phone, name, token } in localStorage
      ↓
Every subsequent API call includes Authorization: Bearer <token>
      ↓
JWTAuthMiddleware validates token on every non-auth request
      ↓
401 returned if token is missing, expired, or invalid
```

## Error Handling

- Missing `Authorization` header on protected route → 401 `{ "detail": "Unauthorized" }`.
- Expired token → 401 `{ "detail": "Unauthorized" }`.
- Invalid signature → 401 `{ "detail": "Unauthorized" }`.
- Frontend receives 401 → logs the user out and redirects to login screen.

## Security Considerations

- `JWT_SECRET` must be a strong random string (minimum 32 characters), stored only in `.env` and never committed to git.
- localStorage is readable by JavaScript (XSS risk) but acceptable for this app given the controlled, closed user base and mobile-web context.
- No endpoint exposes another user's data — the `user_id` in the JWT payload is the authoritative identity for all data access.

## Dependencies

- **Backend**: `python-jose[cryptography]` added to `pyproject.toml`.
- **Frontend**: no new dependencies.

## Testing

- E2E test `tests/e2e/test_opcao1_whatsapp_otp.py` extended to:
  - Assert `access_token` is present in the verify response.
  - Assert a protected endpoint (`/profile/{user_id}`) succeeds with the token.
  - Assert a protected endpoint returns 401 without a token.
  - Assert a protected endpoint returns 401 with an expired/invalid token.

## Out of Scope

- Refresh tokens.
- Token revocation.
- httpOnly cookies.
- Per-user role or permission claims in the JWT payload.

#!/usr/bin/env bash
# Run the content console locally against the HOMOLOGATION database.
# Never points at production: backend/.env (production) is only a fallback for
# unset variables, and DATABASE_URL is set here and checked before starting.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOMOLOG_REF="lgpniurbguguragmubui"
KEYCHAIN_SERVICE="parrot-trips-homolog-supabase-db"
API_PORT="${CONSOLE_HOMOLOG_API_PORT:-8010}"
WEB_PORT="${CONSOLE_HOMOLOG_WEB_PORT:-5180}"

PASSWORD="$(security find-generic-password -s "$KEYCHAIN_SERVICE" -a postgres -w)"
export DATABASE_URL="postgresql+asyncpg://postgres:${PASSWORD}@db.${HOMOLOG_REF}.supabase.co:5432/postgres"
case "$DATABASE_URL" in
  *"@db.${HOMOLOG_REF}.supabase.co"*) ;;
  *) echo "ERROR: DATABASE_URL is not the homologation database. Aborting." >&2; exit 1 ;;
esac

export APP_ENV=development
export ENABLE_CONSOLE_LOCAL=true
export CORS_ALLOWED_ORIGINS="http://localhost:${WEB_PORT}"

cleanup() { [ -n "${API_PID:-}" ] && kill "$API_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo "Backend (homologation DB) on http://localhost:${API_PORT}"
(cd "$ROOT/backend" && env/bin/uvicorn app.main:app --port "$API_PORT") &
API_PID=$!

echo "Console on http://localhost:${WEB_PORT}  (local login, homologation data)"
cd "$ROOT/console"
VITE_API_URL="http://localhost:${API_PORT}" \
VITE_ENABLE_CONSOLE_LOCAL=true \
VITE_ALLOWED_EMAIL_DOMAIN=parrottrips.com \
  npx vite --port "$WEB_PORT" --strictPort

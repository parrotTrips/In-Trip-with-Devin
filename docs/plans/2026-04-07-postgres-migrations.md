# PostgreSQL Migrations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the SQLite bootstrap with PostgreSQL, SQLAlchemy, and Alembic, and move the active backend to the approved relational model.

**Architecture:** The work starts by replacing file-based SQLite configuration with an async PostgreSQL session layer. It then introduces SQLAlchemy models that mirror the approved DBML plus `otp_codes`, adds an Alembic initial migration to create the schema, ports the active services and routers from `aiosqlite` to `AsyncSession`, and finally rewrites the backend tests around the new persistence model.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x async ORM, Alembic, PostgreSQL, pytest

---

### Task 1: Replace SQLite configuration with PostgreSQL session infrastructure

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/.env.example`
- Modify: `backend/app/core/config.py`
- Delete: `backend/app/db/database.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Modify: `backend/app/main.py`

**Step 1: Write the failing test**

Add a test in `backend/tests/test_database_setup.py` that imports the database session helpers and asserts:
- `DATABASE_URL` is read from the environment
- the app startup no longer calls a table-creation helper
- the session module exposes an async engine/session factory

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_database_setup.py -q`
Expected: FAIL because the code still exposes SQLite path helpers and `init_db`.

**Step 3: Write minimal implementation**

- Add `sqlalchemy`, `alembic`, `asyncpg`, and `greenlet` to `backend/pyproject.toml`
- Replace `DATABASE_PATH` config with `DATABASE_URL`
- Create `backend/app/db/base.py` with the declarative base and naming convention
- Create `backend/app/db/session.py` with `create_async_engine`, `async_sessionmaker`, `get_db_session`, and a helper to dispose the engine in tests
- Remove SQLite bootstrap logic by deleting `backend/app/db/database.py`
- Update `backend/app/main.py` so startup no longer creates tables automatically

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_database_setup.py -q`
Expected: PASS with assertions now targeting Postgres session infrastructure.

**Step 5: Commit**

```bash
git add backend/pyproject.toml backend/.env.example backend/app/core/config.py backend/app/db/base.py backend/app/db/session.py backend/app/main.py backend/tests/test_database_setup.py
git commit -m "refactor: add postgres session infrastructure"
```

### Task 2: Add SQLAlchemy models for the approved schema

**Files:**
- Create: `backend/app/db/models/__init__.py`
- Create: `backend/app/db/models/user.py`
- Create: `backend/app/db/models/trip.py`
- Create: `backend/app/db/models/traveler.py`
- Create: `backend/app/db/models/media.py`
- Create: `backend/app/db/models/progress.py`
- Create: `backend/app/db/models/auth.py`
- Modify: `backend/app/db/base.py`

**Step 1: Write the failing test**

Add a metadata test in `backend/tests/test_database_setup.py` that imports the declarative metadata and asserts the presence of the expected tables:
- `users`
- `trips`
- `trip_travelers`
- `traveler_profiles`
- `traveler_products`
- `trip_phases`
- `trip_phase_checklist_items`
- `trip_phase_links`
- `trip_activities`
- `media_assets`
- `activity_media`
- `traveler_checklist_progress`
- `traveler_phase_progress`
- `otp_codes`

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_database_setup.py -q`
Expected: FAIL because the models and metadata tables do not exist yet.

**Step 3: Write minimal implementation**

- Create one SQLAlchemy model per domain area using UUID primary keys
- Map foreign keys, one-to-one uniqueness, composite uniqueness, and timestamp columns to match `docs/db/parrot-trips-erd.dbml`
- Add `otp_codes` as an operational model used by authentication
- Ensure all models are imported from `backend/app/db/models/__init__.py` so Alembic sees the full metadata

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_database_setup.py -q`
Expected: PASS with the metadata exposing all approved tables.

**Step 5: Commit**

```bash
git add backend/app/db/base.py backend/app/db/models backend/tests/test_database_setup.py
git commit -m "feat: add sqlalchemy models for postgres schema"
```

### Task 3: Configure Alembic and create the initial migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/20260407_0001_initial_schema.py`
- Modify: `backend/app/db/models/__init__.py`

**Step 1: Write the failing test**

Add a test in `backend/tests/test_database_setup.py` that runs the Alembic upgrade against a temporary test database and asserts that the created tables include the full approved schema plus `otp_codes`.

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_database_setup.py -q`
Expected: FAIL because Alembic is not configured and no migration exists.

**Step 3: Write minimal implementation**

- Add standard Alembic configuration under `backend/alembic*`
- Point `env.py` at the SQLAlchemy metadata
- Hand-write the initial migration so it creates the schema in dependency-safe order
- Include UUID columns, foreign keys, unique indexes, and timestamps in the migration

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_database_setup.py -q`
Expected: PASS and the temporary Postgres database contains the migrated tables.

**Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic backend/tests/test_database_setup.py
git commit -m "feat: add initial alembic migration"
```

### Task 4: Port authentication and user services to SQLAlchemy

**Files:**
- Modify: `backend/app/routers/auth.py`
- Modify: `backend/app/routers/users.py`
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/services/user_service.py`
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/schemas/users.py`
- Modify: `backend/tests/services/test_auth_service.py`
- Modify: `backend/tests/services/test_user_service.py`
- Modify: `backend/tests/integration/test_auth_routes.py`
- Modify: `backend/tests/integration/test_user_routes.py`

**Step 1: Write the failing test**

Update auth/user service and route tests so they create data through the Postgres session fixture and assert:
- OTP creation persists in `otp_codes`
- OTP verification marks the code as used
- first login creates a `users` row with UUID
- user fetch/update work through SQLAlchemy-backed persistence

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/services/test_auth_service.py backend/tests/services/test_user_service.py backend/tests/integration/test_auth_routes.py backend/tests/integration/test_user_routes.py -q`
Expected: FAIL because the services still depend on `aiosqlite` and integer-based rows.

**Step 3: Write minimal implementation**

- Inject `AsyncSession` into the auth and user routes
- Rewrite `auth_service` to use SQLAlchemy selects/inserts/updates against `OTPCode` and `User`
- Rewrite `user_service` to load and update the `User` model
- Preserve the current HTTP response shape where it still makes sense, but return UUID-backed IDs as strings

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/services/test_auth_service.py backend/tests/services/test_user_service.py backend/tests/integration/test_auth_routes.py backend/tests/integration/test_user_routes.py -q`
Expected: PASS with no `aiosqlite` imports remaining in these paths.

**Step 5: Commit**

```bash
git add backend/app/routers/auth.py backend/app/routers/users.py backend/app/services/auth_service.py backend/app/services/user_service.py backend/app/schemas/auth.py backend/app/schemas/users.py backend/tests/services/test_auth_service.py backend/tests/services/test_user_service.py backend/tests/integration/test_auth_routes.py backend/tests/integration/test_user_routes.py
git commit -m "refactor: port auth and user services to sqlalchemy"
```

### Task 5: Port profile and traveler lookup flows to the new trip-traveler model

**Files:**
- Modify: `backend/app/routers/profile.py`
- Modify: `backend/app/services/profile_service.py`
- Modify: `backend/app/schemas/profile.py`
- Modify: `backend/tests/services/test_profile_service.py`
- Modify: `backend/tests/integration/test_profile_routes.py`

**Step 1: Write the failing test**

Update profile tests so they assert:
- profile reads/writes are tied to `trip_traveler_id`
- endpoints that still receive `user_id` and `trip_id` first resolve the matching `trip_travelers` row
- roommate selection only returns travelers for the requested trip

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/services/test_profile_service.py backend/tests/integration/test_profile_routes.py -q`
Expected: FAIL because the current code still uses `user_profiles.user_id` and lists all users globally.

**Step 3: Write minimal implementation**

- Rewrite profile service queries around `TripTraveler`, `TravelerProfile`, `TravelerProduct`, and `User`
- Make the router/service contract explicit where `trip_id` is required to resolve traveler-in-trip data
- Keep the response shape lean, but stop persisting profile records directly by `user_id`

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/services/test_profile_service.py backend/tests/integration/test_profile_routes.py -q`
Expected: PASS with traveler lookups scoped through `trip_travelers`.

**Step 5: Commit**

```bash
git add backend/app/routers/profile.py backend/app/services/profile_service.py backend/app/schemas/profile.py backend/tests/services/test_profile_service.py backend/tests/integration/test_profile_routes.py
git commit -m "refactor: port traveler profile flows to trip travelers"
```

### Task 6: Port checklist and phase progress to the new progress tables

**Files:**
- Modify: `backend/app/routers/checklist.py`
- Modify: `backend/app/services/checklist_service.py`
- Modify: `backend/app/schemas/checklist.py`
- Modify: `backend/tests/services/test_checklist_service.py`
- Modify: `backend/tests/integration/test_checklist_routes.py`

**Step 1: Write the failing test**

Update checklist tests so they assert:
- checklist progress persists in `traveler_checklist_progress`
- phase completion persists in `traveler_phase_progress`
- upserts are unique by `(trip_traveler_id, trip_phase_checklist_item_id)` and `(trip_traveler_id, trip_phase_id)`
- service resolution starts from `user_id + trip_id` only when necessary, then writes through the new foreign keys

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/services/test_checklist_service.py backend/tests/integration/test_checklist_routes.py -q`
Expected: FAIL because the current code still writes to `checklist_progress` and `phase_completion`.

**Step 3: Write minimal implementation**

- Rewrite checklist service logic around the progress models and `TripTraveler`
- Use PostgreSQL-compatible upsert behavior through SQLAlchemy / dialect helpers
- Remove references to the legacy SQLite table names and item identifiers stored as plain text

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/services/test_checklist_service.py backend/tests/integration/test_checklist_routes.py -q`
Expected: PASS with progress stored in the new tables.

**Step 5: Commit**

```bash
git add backend/app/routers/checklist.py backend/app/services/checklist_service.py backend/app/schemas/checklist.py backend/tests/services/test_checklist_service.py backend/tests/integration/test_checklist_routes.py
git commit -m "refactor: port checklist progress to postgres schema"
```

### Task 7: Remove SQLite-specific code and verify the backend end-to-end

**Files:**
- Modify: `backend/tests/test_database_setup.py`
- Modify: `backend/README.md`
- Modify: `backend/.env.example`

**Step 1: Write the failing test**

Add/adjust assertions so the backend test suite fails if:
- `aiosqlite` is still imported in active backend code
- `DATABASE_PATH` is still documented as the runtime database configuration

**Step 2: Run test to verify it fails**

Run: `rg -n 'aiosqlite|DATABASE_PATH|init_db\\(' backend/app backend/tests backend/.env.example backend/README.md`
Expected: FAILING SIGNAL with active matches before cleanup.

**Step 3: Write minimal implementation**

- Remove leftover SQLite-only references from code and docs
- Document Postgres setup, Alembic usage, and test expectations in `backend/README.md`
- Keep `.env.example` aligned with the new runtime configuration

**Step 4: Run test to verify it passes**

Run: `rg -n 'aiosqlite|DATABASE_PATH|init_db\\(' backend/app backend/tests backend/.env.example backend/README.md`
Expected: no matches in active backend files.

**Step 5: Commit**

```bash
git add backend/tests/test_database_setup.py backend/README.md backend/.env.example
git commit -m "docs: remove sqlite setup references"
```

### Task 8: Run the verification suite

**Files:**
- Modify: `backend/tests/conftest.py`

**Step 1: Write the failing test**

Create `backend/tests/conftest.py` with Postgres test fixtures for:
- temporary database URL resolution
- Alembic upgrade setup
- async SQLAlchemy session provisioning

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests -q`
Expected: FAIL until the fixtures and converted tests are fully wired.

**Step 3: Write minimal implementation**

- Add reusable pytest fixtures for migrated Postgres-backed tests
- Ensure route tests and service tests share the same migrated schema setup

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests -q`
Expected: PASS for the converted backend suite.

**Step 5: Commit**

```bash
git add backend/tests/conftest.py backend/tests
git commit -m "test: add postgres integration fixtures"
```

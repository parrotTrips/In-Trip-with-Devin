# PostgreSQL Migrations Design

**Context**

The active backend still initializes a simplified SQLite schema in code through `backend/app/db/database.py` and accesses it directly with `aiosqlite`. The approved database model now lives in `MODELO_BANCO_DE_DADOS/` and `docs/db/parrot-trips-erd.dbml`, targets PostgreSQL, uses UUID primary keys, and centers traveler state around `trip_travelers`.

**Goal**

Replace the current SQLite bootstrap with a PostgreSQL foundation based on SQLAlchemy and Alembic, and adapt the active backend so it persists against the new relational model from day one.

**Approved Scope**

- Add PostgreSQL configuration through `DATABASE_URL`
- Introduce SQLAlchemy 2.x async engine, session management, and declarative models
- Add Alembic configuration and a single initial migration for the approved schema
- Include `otp_codes` in the initial schema so the current authentication flow still works
- Adapt the active backend services and routers away from `aiosqlite`
- Update backend tests to validate the new Postgres-backed persistence layer
- Assume a brand-new database with no data migration from SQLite

**Modeling Decisions**

- `docs/db/parrot-trips-erd.dbml` is the source of truth for the main relational model
- PostgreSQL is the target datastore now; SQLite compatibility is not preserved
- UUIDs are the canonical identifiers for domain tables
- `trip_travelers` remains the central participation entity and owns traveler-in-trip state
- Temporary API compatibility is acceptable at the HTTP layer where useful, but persistence must use the new model internally
- `otp_codes` remains as an operational table even though it is not part of the current DBML artifact

**Architecture**

The implementation is split into four layers. First, configuration and database wiring move from file-path-based SQLite setup to an async PostgreSQL engine built from `DATABASE_URL`, with FastAPI dependencies providing `AsyncSession` instances. Second, the backend gains explicit SQLAlchemy models that mirror the approved PostgreSQL schema, including relationships and uniqueness constraints. Third, Alembic becomes the only schema-management path, with one initial migration creating the entire database from zero. Fourth, the existing services move off raw `aiosqlite` statements and onto SQLAlchemy-based persistence, resolving `trip_travelers` wherever current endpoints still identify a traveler by `user_id` plus `trip_id`.

**Data Flow**

- Application startup no longer creates tables automatically
- Environments provide `DATABASE_URL`
- Alembic migrations create and evolve the schema
- Requests receive `AsyncSession` through FastAPI dependencies
- Services perform reads and writes through SQLAlchemy models and transactions
- Profile and progress endpoints resolve the relevant `trip_traveler` row before touching traveler-specific tables

**Error Handling**

- Return `404` when required `user`, `trip`, or `trip_traveler` records are missing
- Surface predictable business conflicts as `400` or `409` when appropriate
- Keep structural integrity in PostgreSQL through foreign keys, unique constraints, and non-null columns
- Roll back failed transactions through session handling rather than partial manual commits

**Testing**

- Replace SQLite-specific schema setup tests with Postgres-oriented database bootstrap tests
- Add coverage for the initial Alembic migration
- Keep route/service coverage for auth, profile, checklist, and phase progress flows
- Verify the new uniqueness and relationship rules around `trip_travelers`

**Out of Scope**

- Migrating legacy SQLite data into PostgreSQL
- Reworking unrelated frontend behavior
- Expanding the domain beyond the approved DBML and the operational `otp_codes` table
- Adding analytics or previously removed modules back into the schema

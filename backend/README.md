## Backend Setup

This backend now runs on PostgreSQL through SQLAlchemy async sessions and Alembic migrations.

### Environment

Set the runtime database through `DATABASE_URL`.

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/parrot_trips
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_TEMPLATE_NAME=intripauth
```

### Install

```bash
poetry install
```

### Run Migrations

Create the schema with Alembic before starting the API:

```bash
poetry run alembic upgrade head
```

### Run the API

```bash
poetry run fastapi dev app/main.py
```

### Run Tests

The backend test suite expects PostgreSQL tooling (`initdb`, `pg_ctl`, `createdb`) to be
available in `PATH` or through `POSTGRES_BIN_DIR`. Tests provision a temporary migrated
database automatically.

```bash
poetry run pytest tests -q
```

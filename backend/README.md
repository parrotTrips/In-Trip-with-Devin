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

---

## Makefile (atalhos de desenvolvimento)

Com a env ativada (`source env/bin/activate`), os comandos abaixo estão disponíveis dentro de `backend/`:

| Comando | O que faz |
|---|---|
| `make dev` | Para o backend anterior e sobe na porta 8000 com reload |
| `make stop` | Para o backend |
| `make kill-port` | Libera a porta 8000 se estiver travada |
| `make test` | Roda todos os testes |
| `make test-middleware` | Roda só os testes do JWT middleware |
| `make e2e PHONE=+5511999999999` | Roda o teste E2E de autenticação WhatsApp OTP + JWT |
| `make migrate` | Aplica migrations Alembic |

### Fluxo E2E (WhatsApp OTP + JWT)

**Terminal 1 — subir o backend:**
```bash
make kill-port
make dev
```

**Terminal 2 — rodar o teste:**
```bash
make e2e PHONE=+5512991296651
```

O teste valida automaticamente: geração do JWT, bloqueio de rotas sem token, aceitação do token válido e rejeição de token inválido.

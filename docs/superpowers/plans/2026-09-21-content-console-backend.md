# Content Console — Backend API (Fatia A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expor uma API autenticada `/console` que permite criar, editar, ordenar, publicar e excluir fases pré-trip com seus itens de checklist e links, sem alterar nada do que existe.

**Architecture:** Router FastAPI novo (`/console`), protegido pelo `JWTAuthMiddleware` que já existe, mais uma checagem de `role = 'admin'` por endpoint. Lógica em `console_service.py`, contratos em `schemas/console.py`. Rascunho e publicação usam a coluna `is_visible` de `trip_phases`, que já é filtrada pelo app do viajante e pelo staff.

**Tech Stack:** Python, FastAPI, SQLAlchemy async, asyncpg, Pydantic v2, pytest com Postgres real.

**Spec:** `docs/superpowers/specs/2026-09-21-content-console-design.md`

## Global Constraints

- **Não alterar** `app/routers/admin.py`, `google-apps-script/Code.gs`, `scripts/import_trip_content.py`, nem qualquer arquivo do app do viajante.
- **Não adicionar** `/console` a `_PUBLIC_PREFIXES` em `app/middleware/auth.py`. O prefixo deve permanecer protegido pelo JWT.
- **Nenhuma migration.** `users.role` é `Text` sem CHECK constraint; o valor `admin` é aceito como dado.
- Toda fase criada nasce com `is_visible = false` e `phase_type = 'pre-trip'`.
- Todo endpoint responde `401` sem token e `403` para `role` diferente de `admin`.
- Testes rodam com `.venv/bin/python -m pytest` a partir de `backend/`.
- TDD obrigatório: escrever o teste, vê-lo falhar pelo motivo certo, só então implementar.
- **Imports:** cada tarefa acrescenta funções a `console_service.py` e schemas a `schemas/console.py`. Ao adicionar uma rota, inclua a função e o schema correspondentes nos imports no topo de `app/routers/console.py` — o plano mostra o corpo das rotas, não repete o bloco de imports a cada tarefa.

---

### Task 1: Fundação — router, autorização e listagem de viagens

**Files:**
- Create: `backend/app/routers/console.py`
- Create: `backend/app/services/console_service.py`
- Create: `backend/tests/integration/test_console_routes.py`
- Modify: `backend/app/main.py:16` (import) e `:41` (include_router)

**Interfaces:**
- Consumes: `get_db_session` de `app.db.session`; `JWTAuthMiddleware` já registrado.
- Produces:
  - `require_admin(request: Request, session: AsyncSession) -> str` — retorna o `user_id` ou levanta `HTTPException(403)`. Usada por todas as tarefas seguintes.
  - `GET /console/trips` → `{"trips": [{"trip_uuid": str, "title": str, "start_date": str, "end_date": str}]}`

- [ ] **Step 1: Escrever os testes que falham**

```python
# backend/tests/integration/test_console_routes.py
import asyncio
from datetime import date

from sqlalchemy import text

from app.db.models.user import User


async def _seed_admin_and_trip(session_factory):
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": "console-test",
                "title": "Console Test Trip",
                "dest": "Brazil",
                "sd": date(2027, 7, 1),
                "ed": date(2027, 7, 10),
            },
        )
        session.add_all([
            User(phone="+5511777000001", full_name="Admin", status="active", role="admin"),
            User(phone="+5511777000002", full_name="Trav", status="active", role="traveler"),
        ])
        await session.commit()


def _auth(client, phone: str) -> dict:
    otp_res = client.post("/auth/request-otp", json={"phone": phone})
    verify_res = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_res.json()["debug_code"]},
    )
    return {"Authorization": f"Bearer {verify_res.json()['access_token']}"}


def test_console_trips_requires_a_token(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    assert client.get("/console/trips").status_code == 401


def test_console_trips_rejects_non_admin(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000002")
    assert client.get("/console/trips", headers=headers).status_code == 403


def test_console_trips_lists_trips_for_admin(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    res = client.get("/console/trips", headers=headers)
    assert res.status_code == 200
    assert "console-test" in [t["trip_uuid"] for t in res.json()["trips"]]
```

- [ ] **Step 2: Rodar e verificar que falham**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q`
Expected: FAIL — os três testes retornam `404`, porque `/console/trips` ainda não existe.

- [ ] **Step 3: Implementar o serviço**

```python
# backend/app/services/console_service.py
"""Console service: admin-authenticated trip content editing."""

from __future__ import annotations

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def require_admin(request: Request, session: AsyncSession) -> str:
    """Return the caller's user_id, or raise 403 if they are not an admin."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    role = await session.scalar(
        text("SELECT role FROM users WHERE id = CAST(:user_id AS uuid)"),
        {"user_id": user_id},
    )
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return str(user_id)


async def list_trips(session: AsyncSession) -> dict:
    """Return active trips (end_date today or later, or null)."""
    rows = await session.execute(
        text("""
            SELECT trip_uuid, title, start_date, end_date
            FROM wetravel_trips
            WHERE end_date IS NULL OR end_date::date >= CURRENT_DATE
            ORDER BY start_date ASC
        """)
    )
    return {
        "trips": [
            {
                "trip_uuid": r.trip_uuid,
                "title": r.title,
                "start_date": str(r.start_date) if r.start_date else None,
                "end_date": str(r.end_date) if r.end_date else None,
            }
            for r in rows
        ]
    }
```

- [ ] **Step 4: Implementar o router**

```python
# backend/app/routers/console.py
"""Console HTTP routes — requires JWT with role=admin."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.console_service import list_trips, require_admin

router = APIRouter(prefix="/console", tags=["console"])


@router.get("/trips")
async def list_trips_handler(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return active trips available for content editing."""
    await require_admin(request, session)
    return await list_trips(session)
```

- [ ] **Step 5: Registrar o router**

Em `backend/app/main.py`, adicionar o import junto aos outros (ordem alfabética, após `from app.routers.checklist import ...`):

```python
from app.routers.console import router as console_router
```

E, após `app.include_router(checklist_router)`:

```python
app.include_router(console_router)
```

- [ ] **Step 6: Rodar os testes**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q`
Expected: PASS (3 passed)

- [ ] **Step 7: Rodar a suíte inteira**

Run: `cd backend && .venv/bin/python -m pytest tests/ -q`
Expected: tudo passa, exceto a falha pré-existente `test_activity_checkins_table_metadata`, que não tem relação com este trabalho.

- [ ] **Step 8: Commit**

```bash
git add backend/app/routers/console.py backend/app/services/console_service.py \
        backend/tests/integration/test_console_routes.py backend/app/main.py
git commit -m "feat(console): add admin-authenticated /console router with trip listing"
```

---

### Task 2: Ler a árvore de fases de uma viagem

**Files:**
- Modify: `backend/app/services/console_service.py`
- Modify: `backend/app/routers/console.py`
- Modify: `backend/tests/integration/test_console_routes.py`

**Interfaces:**
- Consumes: `require_admin` da Task 1.
- Produces: `GET /console/trips/{trip_uuid}/phases` → `{"phases": [{"id", "title", "subtitle", "icon", "short_description", "detailed_description", "sort_order", "is_visible", "checklist": [{"id", "label", "is_required", "sort_order"}], "links": [{"id", "label", "url", "sort_order"}]}]}`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao fim de `test_console_routes.py`:

```python
async def _seed_phase_with_children(session_factory):
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO trip_phases
                    (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                     short_description, detailed_description, sort_order,
                     is_locked_by_default, is_visible, created_at, updated_at)
                VALUES (gen_random_uuid(), 'console-test', 'pre-trip', 'Documentos', 'sub',
                        'passport', 'curta', 'longa', 0, false, true, now(), now())
            """)
        )
        phase_id = await session.scalar(
            text("SELECT id FROM trip_phases WHERE wetravel_trip_uuid='console-test' LIMIT 1")
        )
        await session.execute(
            text("""
                INSERT INTO trip_phase_checklist_items
                    (id, trip_phase_id, label, sort_order, is_required, created_at, updated_at)
                VALUES (gen_random_uuid(), :pid, 'Passaporte', 0, true, now(), now())
            """),
            {"pid": phase_id},
        )
        await session.execute(
            text("""
                INSERT INTO trip_phase_links
                    (id, trip_phase_id, label, url, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), :pid, 'Portal', 'https://example.com', 0, now(), now())
            """),
            {"pid": phase_id},
        )
        await session.commit()


def test_get_phases_returns_checklist_and_links(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")

    res = client.get("/console/trips/console-test/phases", headers=headers)

    assert res.status_code == 200
    phases = res.json()["phases"]
    assert len(phases) == 1
    assert phases[0]["title"] == "Documentos"
    assert phases[0]["is_visible"] is True
    assert [i["label"] for i in phases[0]["checklist"]] == ["Passaporte"]
    assert [l["url"] for l in phases[0]["links"]] == ["https://example.com"]
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py::test_get_phases_returns_checklist_and_links -q`
Expected: FAIL com `404`, porque a rota ainda não existe.

- [ ] **Step 3: Implementar o serviço**

Adicionar a `console_service.py`:

```python
async def get_phases(session: AsyncSession, trip_uuid: str) -> dict:
    """Return pre-trip phases of a trip with their checklist items and links."""
    phase_rows = await session.execute(
        text("""
            SELECT id, title, subtitle, icon, short_description,
                   detailed_description, sort_order, is_visible
            FROM trip_phases
            WHERE wetravel_trip_uuid = :trip_uuid AND phase_type = 'pre-trip'
            ORDER BY sort_order ASC
        """),
        {"trip_uuid": trip_uuid},
    )
    phases = [dict(r._mapping) for r in phase_rows]
    if not phases:
        return {"phases": []}

    # JOIN em vez de passar a lista de ids: `ANY(:ids)` dentro de text() depende de
    # inferência de tipo de array e é frágil; o JOIN pelo trip_uuid é equivalente e seguro.
    checklist_rows = await session.execute(
        text("""
            SELECT i.id, i.trip_phase_id, i.label, i.is_required, i.sort_order
            FROM trip_phase_checklist_items i
            JOIN trip_phases p ON p.id = i.trip_phase_id
            WHERE p.wetravel_trip_uuid = :trip_uuid AND p.phase_type = 'pre-trip'
            ORDER BY i.sort_order ASC
        """),
        {"trip_uuid": trip_uuid},
    )
    link_rows = await session.execute(
        text("""
            SELECT l.id, l.trip_phase_id, l.label, l.url, l.sort_order
            FROM trip_phase_links l
            JOIN trip_phases p ON p.id = l.trip_phase_id
            WHERE p.wetravel_trip_uuid = :trip_uuid AND p.phase_type = 'pre-trip'
            ORDER BY l.sort_order ASC
        """),
        {"trip_uuid": trip_uuid},
    )

    by_phase_checklist: dict = {}
    for r in checklist_rows:
        by_phase_checklist.setdefault(r.trip_phase_id, []).append({
            "id": str(r.id), "label": r.label,
            "is_required": r.is_required, "sort_order": r.sort_order,
        })
    by_phase_links: dict = {}
    for r in link_rows:
        by_phase_links.setdefault(r.trip_phase_id, []).append({
            "id": str(r.id), "label": r.label,
            "url": r.url, "sort_order": r.sort_order,
        })

    return {
        "phases": [
            {
                **{k: (str(v) if k == "id" else v) for k, v in p.items()},
                "checklist": by_phase_checklist.get(p["id"], []),
                "links": by_phase_links.get(p["id"], []),
            }
            for p in phases
        ]
    }
```

- [ ] **Step 4: Implementar a rota**

Adicionar a `console.py` (e incluir `get_phases` no import de `console_service`):

```python
@router.get("/trips/{trip_uuid}/phases")
async def get_phases_handler(
    trip_uuid: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return pre-trip phases with checklist items and links."""
    await require_admin(request, session)
    return await get_phases(session, trip_uuid)
```

- [ ] **Step 5: Rodar os testes**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q`
Expected: PASS (4 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/console_service.py backend/app/routers/console.py \
        backend/tests/integration/test_console_routes.py
git commit -m "feat(console): read phase tree with checklist and links"
```

---

### Task 3: Criar fase — nasce em rascunho e invisível para o viajante

**Files:**
- Create: `backend/app/schemas/console.py`
- Modify: `backend/app/services/console_service.py`
- Modify: `backend/app/routers/console.py`
- Modify: `backend/tests/integration/test_console_routes.py`

**Interfaces:**
- Consumes: `require_admin`, `get_phases`.
- Produces:
  - `PhaseCreate` (Pydantic): `title: str`, `subtitle: str | None = None`, `icon: str | None = None`, `short_description: str = ""`, `detailed_description: str | None = None`
  - `POST /console/trips/{trip_uuid}/phases` → `{"id": str, "is_visible": False}`

- [ ] **Step 1: Escrever o teste que falha**

O ponto central deste teste é que a fase criada **não** aparece para o viajante. Adicionar:

```python
def test_created_phase_starts_invisible_to_travelers(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")

    res = client.post(
        "/console/trips/console-test/phases",
        headers=headers,
        json={"title": "Nova Fase", "short_description": "curta"},
    )

    assert res.status_code == 200
    assert res.json()["is_visible"] is False

    # aparece para o admin
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert [p["title"] for p in phases] == ["Nova Fase"]

    # mas não para o app do viajante
    async def _count_visible():
        async with session_factory() as session:
            return await session.scalar(
                text("""
                    SELECT count(*) FROM trip_phases
                    WHERE wetravel_trip_uuid='console-test' AND is_visible IS TRUE
                """)
            )

    assert asyncio.run(_count_visible()) == 0
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py::test_created_phase_starts_invisible_to_travelers -q`
Expected: FAIL com `405` ou `404` — o verbo POST não existe na rota.

- [ ] **Step 3: Criar os schemas**

```python
# backend/app/schemas/console.py
"""Pydantic contracts for the console API."""

from __future__ import annotations

from pydantic import BaseModel


class PhaseCreate(BaseModel):
    title: str
    subtitle: str | None = None
    icon: str | None = None
    short_description: str = ""
    detailed_description: str | None = None
```

- [ ] **Step 4: Implementar o serviço**

Adicionar a `console_service.py`:

```python
async def create_phase(session: AsyncSession, trip_uuid: str, data: dict) -> dict:
    """Create a pre-trip phase in draft state, appended at the end."""
    next_order = await session.scalar(
        text("""
            SELECT COALESCE(MAX(sort_order) + 1, 0) FROM trip_phases
            WHERE wetravel_trip_uuid = :trip_uuid AND phase_type = 'pre-trip'
        """),
        {"trip_uuid": trip_uuid},
    )
    phase_id = await session.scalar(
        text("""
            INSERT INTO trip_phases
                (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                 short_description, detailed_description, sort_order,
                 is_locked_by_default, is_visible, created_at, updated_at)
            VALUES (gen_random_uuid(), :trip_uuid, 'pre-trip', :title, :subtitle, :icon,
                    :short_description, :detailed_description, :sort_order,
                    false, false, now(), now())
            RETURNING id
        """),
        {"trip_uuid": trip_uuid, "sort_order": next_order, **data},
    )
    await session.commit()
    return {"id": str(phase_id), "is_visible": False}
```

- [ ] **Step 5: Implementar a rota**

```python
@router.post("/trips/{trip_uuid}/phases")
async def create_phase_handler(
    trip_uuid: str,
    body: PhaseCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Create a pre-trip phase in draft state."""
    await require_admin(request, session)
    return await create_phase(session, trip_uuid, body.model_dump())
```

- [ ] **Step 6: Rodar os testes**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q`
Expected: PASS (5 passed)

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/console.py backend/app/services/console_service.py \
        backend/app/routers/console.py backend/tests/integration/test_console_routes.py
git commit -m "feat(console): create pre-trip phases in draft state"
```

---

### Task 4: Editar fase, publicar e despublicar

**Files:**
- Modify: `backend/app/schemas/console.py`
- Modify: `backend/app/services/console_service.py`
- Modify: `backend/app/routers/console.py`
- Modify: `backend/tests/integration/test_console_routes.py`

**Interfaces:**
- Produces:
  - `PhaseUpdate` (Pydantic, todos opcionais): `title`, `subtitle`, `icon`, `short_description`, `detailed_description`
  - `PATCH /console/phases/{phase_id}` → `{"id": str, "updated": True}`
  - `POST /console/phases/{phase_id}/publish` → `{"id": str, "is_visible": True}`
  - `POST /console/phases/{phase_id}/unpublish` → `{"id": str, "is_visible": False}`

- [ ] **Step 1: Escrever os testes que falham**

```python
def test_patch_phase_updates_only_provided_fields(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.post(
        "/console/trips/console-test/phases",
        headers=headers,
        json={"title": "Antigo", "short_description": "curta"},
    ).json()["id"]

    res = client.patch(f"/console/phases/{phase_id}", headers=headers, json={"title": "Novo"})

    assert res.status_code == 200
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert phases[0]["title"] == "Novo"
    assert phases[0]["short_description"] == "curta"


def test_publish_and_unpublish_toggle_visibility(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.post(
        "/console/trips/console-test/phases",
        headers=headers,
        json={"title": "Fase", "short_description": "curta"},
    ).json()["id"]

    assert client.post(f"/console/phases/{phase_id}/publish", headers=headers).json()["is_visible"] is True
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert phases[0]["is_visible"] is True

    assert client.post(f"/console/phases/{phase_id}/unpublish", headers=headers).json()["is_visible"] is False
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert phases[0]["is_visible"] is False
```

- [ ] **Step 2: Rodar e verificar que falham**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q -k "patch_phase or publish_and_unpublish"`
Expected: FAIL com `404`/`405`.

- [ ] **Step 3: Adicionar o schema**

Em `backend/app/schemas/console.py`:

```python
class PhaseUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    icon: str | None = None
    short_description: str | None = None
    detailed_description: str | None = None
```

- [ ] **Step 4: Implementar o serviço**

```python
_PHASE_UPDATABLE = ("title", "subtitle", "icon", "short_description", "detailed_description")


async def update_phase(session: AsyncSession, phase_id: str, data: dict) -> dict:
    """Update only the fields explicitly provided."""
    fields = {k: v for k, v in data.items() if k in _PHASE_UPDATABLE and v is not None}
    if not fields:
        return {"id": phase_id, "updated": False}

    assignments = ", ".join(f"{k} = :{k}" for k in fields)
    result = await session.execute(
        text(f"UPDATE trip_phases SET {assignments}, updated_at = now() "
             f"WHERE id = CAST(:phase_id AS uuid)"),
        {"phase_id": phase_id, **fields},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Phase not found")
    await session.commit()
    return {"id": phase_id, "updated": True}


async def set_phase_visibility(session: AsyncSession, phase_id: str, is_visible: bool) -> dict:
    """Publish (visible) or unpublish (draft) a phase."""
    result = await session.execute(
        text("UPDATE trip_phases SET is_visible = :is_visible, updated_at = now() "
             "WHERE id = CAST(:phase_id AS uuid)"),
        {"phase_id": phase_id, "is_visible": is_visible},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Phase not found")
    await session.commit()
    return {"id": phase_id, "is_visible": is_visible}
```

- [ ] **Step 5: Implementar as rotas**

```python
@router.patch("/phases/{phase_id}")
async def update_phase_handler(
    phase_id: str,
    body: PhaseUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Update phase fields."""
    await require_admin(request, session)
    return await update_phase(session, phase_id, body.model_dump(exclude_unset=True))


@router.post("/phases/{phase_id}/publish")
async def publish_phase_handler(
    phase_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Make the phase visible to travelers and staff."""
    await require_admin(request, session)
    return await set_phase_visibility(session, phase_id, True)


@router.post("/phases/{phase_id}/unpublish")
async def unpublish_phase_handler(
    phase_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the phase to draft state."""
    await require_admin(request, session)
    return await set_phase_visibility(session, phase_id, False)
```

- [ ] **Step 6: Rodar os testes**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q`
Expected: PASS (7 passed)

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/console.py backend/app/services/console_service.py \
        backend/app/routers/console.py backend/tests/integration/test_console_routes.py
git commit -m "feat(console): edit phases and toggle publication"
```

---

### Task 5: Excluir fase, recusando quando houver atividades

**Files:**
- Modify: `backend/app/services/console_service.py`
- Modify: `backend/app/routers/console.py`
- Modify: `backend/tests/integration/test_console_routes.py`

**Interfaces:**
- Produces: `DELETE /console/phases/{phase_id}` → `{"id": str, "deleted": True}`, ou `409` se a fase tiver atividades.

- [ ] **Step 1: Escrever os testes que falham**

```python
def test_delete_phase_removes_checklist_and_links(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["id"]

    assert client.delete(f"/console/phases/{phase_id}", headers=headers).status_code == 200

    async def _counts():
        async with session_factory() as session:
            return (
                await session.scalar(text("SELECT count(*) FROM trip_phases WHERE id = CAST(:p AS uuid)"), {"p": phase_id}),
                await session.scalar(text("SELECT count(*) FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)"), {"p": phase_id}),
                await session.scalar(text("SELECT count(*) FROM trip_phase_links WHERE trip_phase_id = CAST(:p AS uuid)"), {"p": phase_id}),
            )

    assert asyncio.run(_counts()) == (0, 0, 0)


def test_delete_phase_refuses_when_activities_exist(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["id"]

    async def _add_activity():
        async with session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO trip_activities
                        (id, trip_phase_id, name, activity_type, short_description,
                         practical_info, sort_order, created_at, updated_at)
                    VALUES (gen_random_uuid(), CAST(:p AS uuid), 'Atividade', 'included',
                            '', '', 0, now(), now())
                """),
                {"p": phase_id},
            )
            await session.commit()

    asyncio.run(_add_activity())

    res = client.delete(f"/console/phases/{phase_id}", headers=headers)

    assert res.status_code == 409
    async def _still_there():
        async with session_factory() as session:
            return await session.scalar(
                text("SELECT count(*) FROM trip_phases WHERE id = CAST(:p AS uuid)"), {"p": phase_id}
            )
    assert asyncio.run(_still_there()) == 1
```

- [ ] **Step 2: Rodar e verificar que falham**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q -k delete_phase`
Expected: FAIL com `405`, porque o verbo DELETE não existe.

- [ ] **Step 3: Implementar o serviço**

```python
async def delete_phase(session: AsyncSession, phase_id: str) -> dict:
    """Delete a phase and its children. Refuse if activities hang off it."""
    exists = await session.scalar(
        text("SELECT count(*) FROM trip_phases WHERE id = CAST(:p AS uuid)"), {"p": phase_id}
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Phase not found")

    activity_count = await session.scalar(
        text("SELECT count(*) FROM trip_activities WHERE trip_phase_id = CAST(:p AS uuid)"),
        {"p": phase_id},
    )
    if activity_count:
        raise HTTPException(
            status_code=409,
            detail=f"Phase has {activity_count} activity(ies); delete them first",
        )

    await session.execute(
        text("""
            DELETE FROM traveler_checklist_progress
            WHERE trip_phase_checklist_item_id IN (
                SELECT id FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)
            )
        """),
        {"p": phase_id},
    )
    for stmt in (
        "DELETE FROM traveler_phase_progress WHERE trip_phase_id = CAST(:p AS uuid)",
        "DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)",
        "DELETE FROM trip_phase_links WHERE trip_phase_id = CAST(:p AS uuid)",
        "DELETE FROM trip_phases WHERE id = CAST(:p AS uuid)",
    ):
        await session.execute(text(stmt), {"p": phase_id})

    await session.commit()
    return {"id": phase_id, "deleted": True}
```

- [ ] **Step 4: Implementar a rota**

```python
@router.delete("/phases/{phase_id}")
async def delete_phase_handler(
    phase_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a phase and its checklist items and links."""
    await require_admin(request, session)
    return await delete_phase(session, phase_id)
```

- [ ] **Step 5: Rodar os testes**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q`
Expected: PASS (9 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/console_service.py backend/app/routers/console.py \
        backend/tests/integration/test_console_routes.py
git commit -m "feat(console): delete phases, refusing when activities exist"
```

---

### Task 6: Substituir checklist e links de uma fase

**Files:**
- Modify: `backend/app/schemas/console.py`
- Modify: `backend/app/services/console_service.py`
- Modify: `backend/app/routers/console.py`
- Modify: `backend/tests/integration/test_console_routes.py`

**Interfaces:**
- Produces:
  - `ChecklistItemIn`: `label: str`, `is_required: bool = False`
  - `ChecklistReplace`: `items: list[ChecklistItemIn]`
  - `LinkIn`: `label: str`, `url: str`
  - `LinkReplace`: `links: list[LinkIn]`
  - `PUT /console/phases/{phase_id}/checklist` → `{"count": int}`
  - `PUT /console/phases/{phase_id}/links` → `{"count": int}`

`sort_order` é sempre o índice na lista enviada — o cliente não envia ordem, a posição é a ordem.

- [ ] **Step 1: Escrever os testes que falham**

```python
def test_put_checklist_replaces_list_and_sets_order(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["id"]

    res = client.put(
        f"/console/phases/{phase_id}/checklist",
        headers=headers,
        json={"items": [
            {"label": "Segundo", "is_required": False},
            {"label": "Primeiro", "is_required": True},
        ]},
    )

    assert res.status_code == 200
    assert res.json()["count"] == 2
    checklist = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["checklist"]
    assert [i["label"] for i in checklist] == ["Segundo", "Primeiro"]
    assert [i["sort_order"] for i in checklist] == [0, 1]
    assert [i["is_required"] for i in checklist] == [False, True]


def test_put_links_replaces_list(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["id"]

    res = client.put(
        f"/console/phases/{phase_id}/links",
        headers=headers,
        json={"links": [{"label": "Novo", "url": "https://novo.example.com"}]},
    )

    assert res.status_code == 200
    links = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["links"]
    assert [l["label"] for l in links] == ["Novo"]
```

- [ ] **Step 2: Rodar e verificar que falham**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q -k "put_checklist or put_links"`
Expected: FAIL com `405`.

- [ ] **Step 3: Adicionar os schemas**

```python
class ChecklistItemIn(BaseModel):
    label: str
    is_required: bool = False


class ChecklistReplace(BaseModel):
    items: list[ChecklistItemIn] = []


class LinkIn(BaseModel):
    label: str
    url: str


class LinkReplace(BaseModel):
    links: list[LinkIn] = []
```

- [ ] **Step 4: Implementar o serviço**

Substituir a lista inteira preserva a ordem sem estados intermediários inconsistentes. O progresso do viajante nos itens antigos é removido junto, porque os itens deixam de existir.

```python
async def replace_checklist(session: AsyncSession, phase_id: str, items: list[dict]) -> dict:
    """Replace every checklist item of the phase; list position becomes sort_order."""
    await session.execute(
        text("""
            DELETE FROM traveler_checklist_progress
            WHERE trip_phase_checklist_item_id IN (
                SELECT id FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)
            )
        """),
        {"p": phase_id},
    )
    await session.execute(
        text("DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = CAST(:p AS uuid)"),
        {"p": phase_id},
    )
    for index, item in enumerate(items):
        await session.execute(
            text("""
                INSERT INTO trip_phase_checklist_items
                    (id, trip_phase_id, label, sort_order, is_required, created_at, updated_at)
                VALUES (gen_random_uuid(), CAST(:p AS uuid), :label, :sort_order, :is_required,
                        now(), now())
            """),
            {"p": phase_id, "label": item["label"],
             "sort_order": index, "is_required": item["is_required"]},
        )
    await session.commit()
    return {"count": len(items)}


async def replace_links(session: AsyncSession, phase_id: str, links: list[dict]) -> dict:
    """Replace every link of the phase; list position becomes sort_order."""
    await session.execute(
        text("DELETE FROM trip_phase_links WHERE trip_phase_id = CAST(:p AS uuid)"),
        {"p": phase_id},
    )
    for index, link in enumerate(links):
        await session.execute(
            text("""
                INSERT INTO trip_phase_links
                    (id, trip_phase_id, label, url, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), CAST(:p AS uuid), :label, :url, :sort_order,
                        now(), now())
            """),
            {"p": phase_id, "label": link["label"], "url": link["url"], "sort_order": index},
        )
    await session.commit()
    return {"count": len(links)}
```

- [ ] **Step 5: Implementar as rotas**

```python
@router.put("/phases/{phase_id}/checklist")
async def replace_checklist_handler(
    phase_id: str,
    body: ChecklistReplace,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Replace the phase checklist with the list sent, in order."""
    await require_admin(request, session)
    return await replace_checklist(session, phase_id, [i.model_dump() for i in body.items])


@router.put("/phases/{phase_id}/links")
async def replace_links_handler(
    phase_id: str,
    body: LinkReplace,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Replace the phase links with the list sent, in order."""
    await require_admin(request, session)
    return await replace_links(session, phase_id, [link.model_dump() for link in body.links])
```

- [ ] **Step 6: Rodar os testes**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q`
Expected: PASS (11 passed)

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/console.py backend/app/services/console_service.py \
        backend/app/routers/console.py backend/tests/integration/test_console_routes.py
git commit -m "feat(console): replace phase checklist and links as ordered lists"
```

---

### Task 7: Reordenar fases

**Files:**
- Modify: `backend/app/schemas/console.py`
- Modify: `backend/app/services/console_service.py`
- Modify: `backend/app/routers/console.py`
- Modify: `backend/tests/integration/test_console_routes.py`

**Interfaces:**
- Produces:
  - `PhaseOrder`: `phase_ids: list[str]`
  - `PUT /console/trips/{trip_uuid}/phases/order` → `{"count": int}`

- [ ] **Step 1: Escrever o teste que falha**

```python
def test_reorder_phases_sets_sort_order_by_position(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    first = client.post("/console/trips/console-test/phases", headers=headers,
                        json={"title": "A", "short_description": ""}).json()["id"]
    second = client.post("/console/trips/console-test/phases", headers=headers,
                         json={"title": "B", "short_description": ""}).json()["id"]

    res = client.put(
        "/console/trips/console-test/phases/order",
        headers=headers,
        json={"phase_ids": [second, first]},
    )

    assert res.status_code == 200
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert [p["title"] for p in phases] == ["B", "A"]
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py::test_reorder_phases_sets_sort_order_by_position -q`
Expected: FAIL com `405`.

- [ ] **Step 3: Adicionar o schema**

```python
class PhaseOrder(BaseModel):
    phase_ids: list[str] = []
```

- [ ] **Step 4: Implementar o serviço**

```python
async def reorder_phases(session: AsyncSession, trip_uuid: str, phase_ids: list[str]) -> dict:
    """Set sort_order from the position of each id in the list."""
    for index, phase_id in enumerate(phase_ids):
        await session.execute(
            text("""
                UPDATE trip_phases SET sort_order = :sort_order, updated_at = now()
                WHERE id = CAST(:phase_id AS uuid) AND wetravel_trip_uuid = :trip_uuid
            """),
            {"sort_order": index, "phase_id": phase_id, "trip_uuid": trip_uuid},
        )
    await session.commit()
    return {"count": len(phase_ids)}
```

- [ ] **Step 5: Implementar a rota**

```python
@router.put("/trips/{trip_uuid}/phases/order")
async def reorder_phases_handler(
    trip_uuid: str,
    body: PhaseOrder,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Reorder the trip phases according to the list sent."""
    await require_admin(request, session)
    return await reorder_phases(session, trip_uuid, body.phase_ids)
```

- [ ] **Step 6: Rodar a suíte inteira**

Run: `cd backend && .venv/bin/python -m pytest tests/ -q`
Expected: tudo passa, exceto a falha pré-existente `test_activity_checkins_table_metadata`.

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/console.py backend/app/services/console_service.py \
        backend/app/routers/console.py backend/tests/integration/test_console_routes.py
git commit -m "feat(console): reorder phases"
```

---

## Depois deste plano

O backend fica completo para a fatia A. O próximo plano (`2026-09-21-content-console-frontend.md`) cobre o app `console/`: scaffold Vite, login OTP com guard de `admin`, tela de viagens com o botão de copiar link de pré-embarque, tela de fases e editor de fase.

Promoção do primeiro admin, a ser feita uma vez no banco:

```sql
UPDATE users SET role = 'admin' WHERE phone = '<telefone>';
```

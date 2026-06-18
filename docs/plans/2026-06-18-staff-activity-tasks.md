# Staff Activity Tasks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let each staff member see only their own operational tasks inside each itinerary activity in the staff app.

**Architecture:** Extend the existing `staff_tasks` table with `trip_activity_id`, import tasks from a new `Tarefas Staff` tab in the staff spreadsheet, and attach authenticated-user-specific tasks to each activity returned by `GET /me/staff/trip`. The frontend renders a compact `My tasks` section inside expanded itinerary activities.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, asyncpg, Google Sheets API import scripts, React/Vite/TypeScript, Vitest, pytest.

---

### Task 1: Add `trip_activity_id` To `staff_tasks`

**Files:**
- Create: `backend/alembic/versions/20260618_0009_add_trip_activity_id_to_staff_tasks.py`
- Modify: `backend/app/db/models/staff.py`
- Test: `backend/tests/test_database_setup.py`

**Step 1: Write the failing metadata test**

Add this test to `backend/tests/test_database_setup.py`:

```python
def test_staff_tasks_has_trip_activity_id_foreign_key():
    reload_module("app.db.models")
    base_module = importlib.import_module("app.db.base")

    staff_tasks = base_module.metadata.tables["staff_tasks"]

    assert "trip_activity_id" in staff_tasks.c
    fk_targets = {
        fk.column.table.name + "." + fk.column.name
        for fk in staff_tasks.c.trip_activity_id.foreign_keys
    }
    assert "trip_activities.id" in fk_targets
```

**Step 2: Run test to verify it fails**

Run:

```bash
cd backend
poetry run pytest tests/test_database_setup.py::test_staff_tasks_has_trip_activity_id_foreign_key -v
```

Expected: FAIL because `trip_activity_id` does not exist on the model.

**Step 3: Update the model**

In `backend/app/db/models/staff.py`, import stays the same and add this field to `StaffTask`:

```python
    trip_activity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_activities.id"), nullable=True
    )
```

Keep it nullable so existing empty/legacy rows do not break migration.

**Step 4: Add migration**

Create `backend/alembic/versions/20260618_0009_add_trip_activity_id_to_staff_tasks.py`:

```python
"""add trip_activity_id to staff_tasks

Revision ID: 20260618_0009
Revises: 20260612_0008
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260618_0009"
down_revision = "20260612_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "staff_tasks",
        sa.Column("trip_activity_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_staff_tasks_trip_activity_id_trip_activities",
        "staff_tasks",
        "trip_activities",
        ["trip_activity_id"],
        ["id"],
    )
    op.create_index(
        "ix_staff_tasks_trip_activity_assignee",
        "staff_tasks",
        ["trip_activity_id", "assigned_to_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_staff_tasks_trip_activity_assignee", table_name="staff_tasks")
    op.drop_constraint(
        "fk_staff_tasks_trip_activity_id_trip_activities",
        "staff_tasks",
        type_="foreignkey",
    )
    op.drop_column("staff_tasks", "trip_activity_id")
```

**Step 5: Run test to verify it passes**

Run:

```bash
cd backend
poetry run pytest tests/test_database_setup.py::test_staff_tasks_has_trip_activity_id_foreign_key -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add backend/alembic/versions/20260618_0009_add_trip_activity_id_to_staff_tasks.py backend/app/db/models/staff.py backend/tests/test_database_setup.py
git commit -m "feat: link staff tasks to trip activities"
```

---

### Task 2: Parse `Tarefas Staff` Rows

**Files:**
- Modify: `backend/scripts/import_staff_content.py`
- Test: `backend/tests/scripts/test_import_staff_content.py`

**Step 1: Create failing parser tests**

Create `backend/tests/scripts/test_import_staff_content.py` if it does not exist:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.import_staff_content import parse_staff_tasks_tab


def test_parse_staff_tasks_tab_basic():
    rows = [
        ["trip_uuid", "dia", "atividade_nome", "staff_phone", "titulo", "descricao", "sort_order"],
        [
            "TEST-2026-FULL",
            "1",
            "Airport Transfer",
            "+5511999990001",
            "Coordenar van 1",
            "Receber viajantes no aeroporto",
            "1",
        ],
    ]

    tasks = parse_staff_tasks_tab(rows)

    assert tasks == [
        {
            "trip_uuid": "TEST-2026-FULL",
            "dia": 1,
            "atividade_nome": "Airport Transfer",
            "staff_phone": "+5511999990001",
            "titulo": "Coordenar van 1",
            "descricao": "Receber viajantes no aeroporto",
            "sort_order": 1,
        }
    ]


def test_parse_staff_tasks_tab_skips_rows_without_title():
    rows = [
        ["trip_uuid", "dia", "atividade_nome", "staff_phone", "titulo", "descricao", "sort_order"],
        ["TEST-2026-FULL", "1", "Airport Transfer", "+5511999990001", "", "Sem titulo", "1"],
    ]

    assert parse_staff_tasks_tab(rows) == []
```

**Step 2: Run parser tests to verify they fail**

Run:

```bash
cd backend
poetry run pytest tests/scripts/test_import_staff_content.py -v
```

Expected: FAIL because `parse_staff_tasks_tab` does not exist.

**Step 3: Implement parser**

In `backend/scripts/import_staff_content.py`, add:

```python
def parse_staff_tasks_tab(rows: list[list[str]]) -> list[dict]:
    """Parse Tarefas Staff tab.

    Columns: trip_uuid, dia, atividade_nome, staff_phone, titulo, descricao, sort_order
    """
    if not rows or len(rows) < 2:
        return []
    header = [h.strip().lower() for h in rows[0]]

    def col(row: list[str], name: str) -> str:
        try:
            idx = header.index(name)
            return row[idx].strip() if idx < len(row) else ""
        except ValueError:
            return ""

    tasks = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        title = col(row, "titulo")
        if not title:
            continue
        try:
            day = int(col(row, "dia") or "0")
        except ValueError:
            day = 0
        try:
            sort_order = int(col(row, "sort_order") or "0")
        except ValueError:
            sort_order = 0
        tasks.append({
            "trip_uuid": col(row, "trip_uuid"),
            "dia": day,
            "atividade_nome": col(row, "atividade_nome"),
            "staff_phone": col(row, "staff_phone"),
            "titulo": title,
            "descricao": col(row, "descricao") or None,
            "sort_order": sort_order,
        })
    return tasks
```

**Step 4: Run parser tests to verify they pass**

Run:

```bash
cd backend
poetry run pytest tests/scripts/test_import_staff_content.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/scripts/import_staff_content.py backend/tests/scripts/test_import_staff_content.py
git commit -m "feat: parse staff activity tasks sheet"
```

---

### Task 3: Import Staff Tasks Into Supabase

**Files:**
- Modify: `backend/scripts/import_staff_content.py`
- Modify: `backend/app/services/admin_service.py`
- Modify: `backend/app/routers/admin.py`
- Test: `backend/tests/scripts/test_import_staff_content.py`

**Step 1: Add failing validation tests for task resolution**

Append to `backend/tests/scripts/test_import_staff_content.py`:

```python
import pytest

from scripts.import_staff_content import StaffTaskImportError, _require_single_row


def test_require_single_row_returns_row():
    row = {"id": "abc"}

    assert _require_single_row([row], "activity", "Airport Transfer") == row


def test_require_single_row_fails_when_missing():
    with pytest.raises(StaffTaskImportError, match="activity not found"):
        _require_single_row([], "activity", "Airport Transfer")


def test_require_single_row_fails_when_duplicate():
    with pytest.raises(StaffTaskImportError, match="activity is ambiguous"):
        _require_single_row([{"id": "a"}, {"id": "b"}], "activity", "Airport Transfer")
```

**Step 2: Run tests to verify they fail**

Run:

```bash
cd backend
poetry run pytest tests/scripts/test_import_staff_content.py -v
```

Expected: FAIL because the helper and exception do not exist.

**Step 3: Implement validation helpers**

In `backend/scripts/import_staff_content.py`, add:

```python
class StaffTaskImportError(ValueError):
    pass


def _require_single_row(rows: list, label: str, lookup: str):
    if len(rows) == 1:
        return rows[0]
    if not rows:
        raise StaffTaskImportError(f"{label} not found: {lookup}")
    raise StaffTaskImportError(f"{label} is ambiguous: {lookup}")
```

**Step 4: Implement DB writer**

In `backend/scripts/import_staff_content.py`, add:

```python
async def write_staff_tasks(conn: asyncpg.Connection, trip_uuid: str, tasks: list[dict]) -> int:
    """Delete existing staff tasks for a trip and insert fresh rows from the sheet."""
    phase_rows = await conn.fetch(
        "SELECT id FROM trip_phases WHERE wetravel_trip_uuid = $1",
        trip_uuid,
    )
    phase_ids = [r["id"] for r in phase_rows]
    if phase_ids:
        await conn.execute(
            "DELETE FROM staff_tasks WHERE trip_phase_id = ANY($1::uuid[])",
            phase_ids,
        )

    inserted = 0
    for task in tasks:
        staff_rows = await conn.fetch(
            "SELECT id FROM users WHERE phone = $1 AND role = 'staff'",
            task["staff_phone"],
        )
        staff = _require_single_row(staff_rows, "staff", task["staff_phone"])

        day_rows = await conn.fetch(
            """
            SELECT id
            FROM trip_phases
            WHERE wetravel_trip_uuid = $1
              AND phase_type = 'in-trip'
              AND sort_order = $2
            """,
            trip_uuid,
            task["dia"] - 1,
        )
        day = _require_single_row(day_rows, "day", str(task["dia"]))

        activity_rows = await conn.fetch(
            """
            SELECT id
            FROM trip_activities
            WHERE trip_phase_id = $1
              AND lower(name) = lower($2)
            """,
            day["id"],
            task["atividade_nome"],
        )
        activity = _require_single_row(activity_rows, "activity", task["atividade_nome"])

        await conn.execute(
            """
            INSERT INTO staff_tasks
                (id, trip_phase_id, trip_activity_id, assigned_to_user_id,
                 title, description, starts_at, sort_order, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NULL, $6, now(), now())
            """,
            day["id"],
            activity["id"],
            staff["id"],
            task["titulo"],
            task["descricao"],
            task["sort_order"],
        )
        inserted += 1

    return inserted
```

Note: this uses `dia - 1` because existing imported in-trip phases use zero-based `sort_order` for day ordering. If the current data proves otherwise during implementation, adjust this lookup and add a regression test.

**Step 5: Wire import flow**

In `import_one`, read `Tarefas Staff`:

```python
tasks_rows = filter_rows_by_trip(read_tab(sheets_svc, sheet_id, "Tarefas Staff"), trip_uuid)
tasks = parse_staff_tasks_tab(tasks_rows)
```

Inside the transaction:

```python
tasks_count = await write_staff_tasks(conn, trip_uuid, tasks)
```

Include in the return payload:

```python
"staff_tasks": tasks_count,
```

In `backend/app/services/admin_service.py`, add `admin_import_staff_tasks(trip_uuid: str)` that imports `filter_rows_by_trip`, `parse_staff_tasks_tab`, `read_tab`, and `write_staff_tasks`, reads `Tarefas Staff`, and returns:

```python
{"status": "ok", "trip_uuid": trip_uuid, "staff_tasks_imported": count}
```

In `backend/app/routers/admin.py`, import `admin_import_staff_tasks` and add:

```python
@router.post("/trips/import-staff-tasks")
async def import_staff_tasks(body: TripUUIDRequest):
    """Import staff activity tasks from the Staff Google Sheet into staff_tasks."""
    try:
        return await admin_import_staff_tasks(body.trip_uuid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
```

**Step 6: Run tests**

Run:

```bash
cd backend
poetry run pytest tests/scripts/test_import_staff_content.py -v
```

Expected: PASS.

**Step 7: Commit**

```bash
git add backend/scripts/import_staff_content.py backend/app/services/admin_service.py backend/app/routers/admin.py backend/tests/scripts/test_import_staff_content.py
git commit -m "feat: import staff tasks from sheet"
```

---

### Task 4: Add Staff Tasks To Staff Trip API

**Files:**
- Modify: `backend/app/routers/staff.py`
- Test: `backend/tests/integration/test_staff_routes.py`

**Step 1: Create failing integration test**

Create `backend/tests/integration/test_staff_routes.py`:

```python
import asyncio

from sqlalchemy import text

from app.db.models.staff import StaffTask
from app.db.models.trip import TripActivity, TripPhase, TripTraveler
from app.db.models.user import User


async def _seed_staff_trip_with_tasks(session_factory):
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": "staff-route-test",
                "title": "Staff Route Test",
                "dest": "Brazil",
                "sd": "2026-07-01",
                "ed": "2026-07-10",
            },
        )
        staff = User(phone="+5511888000001", full_name="Staff One", status="active", role="staff")
        other_staff = User(phone="+5511888000002", full_name="Staff Two", status="active", role="staff")
        session.add_all([staff, other_staff])
        await session.flush()
        session.add(TripTraveler(wetravel_trip_uuid="staff-route-test", user_id=staff.id))

        phase = TripPhase(
            wetravel_trip_uuid="staff-route-test",
            phase_type="in-trip",
            title="Day 1 — Arrival",
            subtitle="Arrival",
            icon="plane-landing",
            short_description="Arrival day",
            detailed_description=None,
            sort_order=0,
            starts_at=None,
            is_locked_by_default=False,
            is_visible=True,
        )
        session.add(phase)
        await session.flush()

        activity = TripActivity(
            trip_phase_id=phase.id,
            name="Airport Transfer",
            activity_type="logistics",
            starts_at=None,
            duration_minutes=None,
            short_description="Airport pickup",
            practical_info=None,
            amount_brl=None,
            sort_order=0,
        )
        session.add(activity)
        await session.flush()

        session.add_all([
            StaffTask(
                trip_phase_id=phase.id,
                trip_activity_id=activity.id,
                assigned_to_user_id=staff.id,
                title="Coordenar van 1",
                description="Receber viajantes no aeroporto",
                starts_at=None,
                sort_order=1,
            ),
            StaffTask(
                trip_phase_id=phase.id,
                trip_activity_id=activity.id,
                assigned_to_user_id=other_staff.id,
                title="Tarefa invisível",
                description="Nao deve aparecer para Staff One",
                starts_at=None,
                sort_order=1,
            ),
        ])
        await session.commit()


def _auth(client, phone: str) -> dict:
    otp_res = client.post("/auth/request-otp", json={"phone": phone})
    verify_res = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_res.json()["debug_code"]},
    )
    return {"Authorization": f"Bearer {verify_res.json()['access_token']}"}


def test_get_staff_trip_includes_only_current_staff_tasks(seeded_client, session_factory):
    asyncio.run(_seed_staff_trip_with_tasks(session_factory))
    headers = _auth(seeded_client, "+5511888000001")

    response = seeded_client.get("/me/staff/trip", headers=headers)

    assert response.status_code == 200
    activity = response.json()["days"][0]["activities"][0]
    assert activity["staff_tasks"] == [
        {
            "id": activity["staff_tasks"][0]["id"],
            "title": "Coordenar van 1",
            "description": "Receber viajantes no aeroporto",
            "sort_order": 1,
        }
    ]
```

**Step 2: Run test to verify it fails**

Run:

```bash
cd backend
poetry run pytest tests/integration/test_staff_routes.py::test_get_staff_trip_includes_only_current_staff_tasks -v
```

Expected: FAIL because activities do not include `staff_tasks`.

**Step 3: Update staff router**

In `backend/app/routers/staff.py`:

- Import `StaffTask`:

```python
from app.db.models.staff import StaffTask, TripContact
```

- After fetching activities, fetch current staff tasks:

```python
activity_ids = [act.id for act in activities]
tasks_by_activity: dict = {}
if activity_ids:
    tasks_result = await session.execute(
        select(StaffTask)
        .where(
            StaffTask.trip_activity_id.in_(activity_ids),
            StaffTask.assigned_to_user_id == user_id,
        )
        .order_by(StaffTask.trip_activity_id, StaffTask.sort_order)
    )
    for task in tasks_result.scalars():
        tasks_by_activity.setdefault(task.trip_activity_id, []).append({
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "sort_order": task.sort_order,
        })
```

- Add `staff_tasks` to each activity payload:

```python
"staff_tasks": tasks_by_activity.get(act.id, []),
```

**Step 4: Run test to verify it passes**

Run:

```bash
cd backend
poetry run pytest tests/integration/test_staff_routes.py::test_get_staff_trip_includes_only_current_staff_tasks -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/routers/staff.py backend/tests/integration/test_staff_routes.py
git commit -m "feat: return current staff tasks in itinerary"
```

---

### Task 5: Update Staff Sheet Creation And Apps Script Menu

**Files:**
- Modify: `backend/scripts/create_staff_sheets.py`
- Modify: `google-apps-script/CodeStaff.gs`

**Step 1: Add staff task sheet constants and examples**

In `backend/scripts/create_staff_sheets.py`, add:

```python
STAFF_TASKS_HEADER = [
    "trip_uuid",
    "dia",
    "atividade_nome",
    "staff_phone",
    "titulo",
    "descricao",
    "sort_order",
]
```

Add example rows:

```python
def _staff_tasks_example_rows(trip_uuid: str) -> list[list]:
    u = trip_uuid
    return [
        [u, 1, "Airport Transfer", "+55 11 99999-0001", "Coordenar van 1", "Receber viajantes no aeroporto e direcionar para a van correta", 1],
        [u, 1, "Airport Transfer", "+55 11 99999-0002", "Confirmar fornecedor", "Falar com motorista e confirmar saída", 1],
    ]
```

In `populate_spreadsheet`, build `staff_tasks_rows` and add:

```python
_add_tab("Tarefas Staff", STAFF_TASKS_HEADER, staff_tasks_rows)
```

**Step 2: Update Apps Script menu**

In `google-apps-script/CodeStaff.gs`:

- Add menu item after contacts:

```javascript
.addItem("Import Staff Tasks → Supabase", "importStaffTasks")
```

- Add function:

```javascript
function importStaffTasks() {
  var trip_uuid = promptForTrip("🦜 Import Staff Tasks → Supabase");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import-staff-tasks", { trip_uuid: trip_uuid }));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}
```

- Add `Tarefas Staff` to `setupSheetHeaders`:

```javascript
{
  name: "Tarefas Staff",
  headers: ["trip_uuid", "dia", "atividade_nome", "staff_phone", "titulo", "descricao", "sort_order"],
  note: "Uma linha por tarefa operacional de um staff dentro de uma atividade do roteiro"
}
```

- Update the final setup message to mention staff tasks.

**Step 3: Verify syntax manually**

Run:

```bash
python -m py_compile backend/scripts/create_staff_sheets.py
```

Expected: no output and exit code 0.

**Step 4: Commit**

```bash
git add backend/scripts/create_staff_sheets.py google-apps-script/CodeStaff.gs
git commit -m "feat: add staff tasks sheet setup"
```

---

### Task 6: Render `My tasks` In Staff App

**Files:**
- Modify: `frontend/src/features/staff/services/staff-api.ts`
- Modify: `frontend/src/features/staff/pages/StaffScreen.tsx`
- Test: `frontend/src/features/staff/StaffScreen.test.tsx`

**Step 1: Update TypeScript types**

In `frontend/src/features/staff/services/staff-api.ts`, add:

```ts
export interface StaffTask {
  id: string;
  title: string;
  description: string | null;
  sort_order: number;
}
```

Add to `StaffActivity`:

```ts
staff_tasks: StaffTask[];
```

**Step 2: Create failing UI test**

Create `frontend/src/features/staff/StaffScreen.test.tsx`:

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import StaffScreen from './pages/StaffScreen';

describe('StaffScreen', () => {
  beforeEach(() => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'staff-1', phone: '+5511888000001', name: 'Marcelo Staff', token: 'tok', role: 'staff' })
    );
    server.use(
      http.get('http://localhost:8000/me/staff/trip', () =>
        HttpResponse.json({
          wetravel_trip_uuid: 'TEST-2026-FULL',
          title: 'Test Trip',
          start_date: '2026-07-01',
          end_date: '2026-07-07',
          days: [
            {
              id: 'day-1',
              title: 'Day 1 — Arrival',
              subtitle: 'Arrival',
              icon: 'plane-landing',
              sort_order: 0,
              starts_at: null,
              activities: [
                {
                  id: 'activity-1',
                  name: 'Airport Transfer',
                  activity_type: 'logistics',
                  starts_at: null,
                  duration_minutes: null,
                  short_description: 'Airport pickup',
                  practical_info: null,
                  amount_brl: null,
                  sort_order: 0,
                  staff_tasks: [
                    {
                      id: 'task-1',
                      title: 'Coordenar van 1',
                      description: 'Receber viajantes no aeroporto',
                      sort_order: 1,
                    },
                  ],
                },
              ],
            },
          ],
        })
      ),
      http.get('http://localhost:8000/me/staff/trip/contacts', () =>
        HttpResponse.json({ wetravel_trip_uuid: 'TEST-2026-FULL', contacts: [] })
      )
    );
  });

  test('shows current staff tasks inside expanded activity', async () => {
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await user.click(await screen.findByText('Day 1 — Arrival'));
    await user.click(await screen.findByText('Airport Transfer'));

    await waitFor(() => {
      expect(screen.getByText('My tasks')).toBeInTheDocument();
    });
    expect(screen.getByText('Coordenar van 1')).toBeInTheDocument();
    expect(screen.getByText('Receber viajantes no aeroporto')).toBeInTheDocument();
  });
});
```

**Step 3: Run UI test to verify it fails**

Run:

```bash
cd frontend
npm test -- StaffScreen.test.tsx --run
```

Expected: FAIL because the UI does not render `My tasks`.

**Step 4: Implement UI**

In `frontend/src/features/staff/pages/StaffScreen.tsx`, inside the expanded activity block, after `amount_brl`, add:

```tsx
{act.staff_tasks?.length > 0 && (
  <div className="bg-white rounded-lg border border-emerald-100 overflow-hidden">
    <div className="px-3 py-2 bg-emerald-50 border-b border-emerald-100">
      <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">My tasks</p>
    </div>
    <div className="divide-y divide-gray-100">
      {act.staff_tasks.map((task) => (
        <div key={task.id} className="px-3 py-2">
          <p className="text-sm font-medium text-gray-800">{task.title}</p>
          {task.description && (
            <p className="text-xs text-gray-500 mt-0.5">{task.description}</p>
          )}
        </div>
      ))}
    </div>
  </div>
)}
```

**Step 5: Run UI test to verify it passes**

Run:

```bash
cd frontend
npm test -- StaffScreen.test.tsx --run
```

Expected: PASS.

**Step 6: Run frontend type/build check**

Run:

```bash
cd frontend
npm run build
```

Expected: PASS.

**Step 7: Commit**

```bash
git add frontend/src/features/staff/services/staff-api.ts frontend/src/features/staff/pages/StaffScreen.tsx frontend/src/features/staff/StaffScreen.test.tsx
git commit -m "feat: show staff tasks in itinerary"
```

---

### Task 7: Validate With Supabase And Test Trip

**Files:**
- No code changes expected.
- Use: `backend/scripts/import_staff_content.py`
- Use: `google-apps-script/CodeStaff.gs`

**Step 1: Apply database migration locally/target environment**

Run:

```bash
cd backend
poetry run alembic upgrade head
```

Expected: migration `20260618_0009` applies successfully.

**Step 2: Add sample rows to `Tarefas Staff`**

In the staff spreadsheet, add rows for `TEST-2026-FULL`:

```text
trip_uuid | dia | atividade_nome | staff_phone | titulo | descricao | sort_order
TEST-2026-FULL | 1 | Airport Transfer | <phone of staff 1> | Coordenar van 1 | Receber viajantes no aeroporto e direcionar para a van correta | 1
TEST-2026-FULL | 1 | Airport Transfer | <phone of staff 2> | Confirmar fornecedor | Falar com motorista e confirmar saída | 1
```

Use actual staff phones already present in the `Staff` tab.

**Step 3: Import staff tasks**

Use the Apps Script menu:

```text
🦜 Parrot Staff → Import Staff Tasks → Supabase
```

Or run the script:

```bash
cd backend
poetry run python scripts/import_staff_content.py --trip-uuid TEST-2026-FULL
```

Expected: result includes `staff_tasks` or `staff_tasks_imported` greater than 0.

**Step 4: Verify DB rows**

Run a read-only query:

```bash
cd backend
uv run --with asyncpg python -c 'import asyncio; import asyncpg
from pathlib import Path
def env_value(key):
    for line in Path(".env").read_text().splitlines():
        if line.startswith(key+"="):
            return line.split("=",1)[1].strip()
async def main():
    url=env_value("DATABASE_URL").replace("postgresql+asyncpg://","postgresql://")
    conn=await asyncpg.connect(url)
    rows=await conn.fetch("""
        SELECT u.full_name, tp.title AS day_title, ta.name AS activity_name, st.title
        FROM staff_tasks st
        JOIN users u ON u.id = st.assigned_to_user_id
        JOIN trip_phases tp ON tp.id = st.trip_phase_id
        JOIN trip_activities ta ON ta.id = st.trip_activity_id
        WHERE tp.wetravel_trip_uuid = $1
        ORDER BY u.full_name, tp.sort_order, ta.sort_order, st.sort_order
    """, "TEST-2026-FULL")
    for r in rows:
        print(dict(r))
    await conn.close()
asyncio.run(main())'
```

Expected: rows show the imported tasks mapped to the correct staff and activity.

**Step 5: Validate in app**

Run the app:

```bash
cd frontend
npm run dev
```

Open the local URL, login as each test staff, and verify:

- the staff can open the Itinerary tab;
- the relevant day/activity appears;
- the activity shows `My tasks`;
- each staff sees only their own tasks.

**Step 6: Commit any validation doc update if needed**

If you add notes to docs:

```bash
git add <doc-path>
git commit -m "docs: record staff tasks validation"
```

Otherwise, no commit is needed.

---

### Final Verification

Run:

```bash
cd backend
poetry run pytest tests/test_database_setup.py tests/scripts/test_import_staff_content.py tests/integration/test_staff_routes.py -v
```

Expected: PASS.

Run:

```bash
cd frontend
npm test -- StaffScreen.test.tsx --run
npm run build
```

Expected: PASS.

Run:

```bash
git status --short
```

Expected: only intentional uncommitted files remain. Do not revert unrelated existing files such as `roadmap.md`, `firebase-debug.log`, `frontend/firebase-debug.log`, or `resume.txt` unless explicitly requested.

# Progress Bar Pre-Trip / In-Trip Split — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the progress bar so it tracks only pre-trip phases (user-driven) before the trip starts, and only in-trip phases (auto-calculated from dates) once the trip begins — plus a script to reset traveler progress.

**Architecture:** Backend adds a new helper `compute_in_trip_phase_completions(phases, now)` that returns date-derived completions for `in-trip` phases without touching the DB. The existing `get_trip_travelers` endpoint enriches `current_phase_id` using this helper when the trip is underway. The frontend `HomeScreen` filters phases by mode (`pre-trip` vs `in-trip`) before passing counts to `ProgressBar` — no API shape changes needed. A new script `reset_traveler_progress.py` deletes all traveler progress rows for a given trip.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy async, pytest, React/TypeScript

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/app/services/trip_service.py` | Modify | Add `compute_in_trip_phase_completions`, update `get_trip_travelers` to use it |
| `backend/tests/services/test_trip_service.py` | Create | Unit tests for `compute_in_trip_phase_completions` and integration test for `get_trip_travelers` |
| `backend/scripts/reset_traveler_progress.py` | Create | CLI script to wipe traveler progress for a trip |
| `frontend/src/features/trip/pages/HomeScreen.tsx` | Modify | Filter phases by mode; pass mode-scoped counts to ProgressBar |

---

## Current behaviour (context)

- `GET /me/trip/travelers` returns `current_phase_id` for each traveler, computed as "first phase with `sort_order > max_completed_phase_sort_order`" across ALL phases (pre-trip + in-trip).
- `ProgressBar` receives `totalPhases = phases.length` (all phases), `currentPhaseOrder = index of current phase in all phases`.
- `computeParrotPhaseId` in `HomeScreen` already finds the in-trip phase whose `starts_at <= today` — this logic is correct and does NOT change.
- The trip's `start_date` is available in `tripInfo.start_date` on the frontend.

---

## What changes

### Backend

`compute_in_trip_phase_completions(phases, now)` — pure function, no DB:
- Input: list of phase dicts (each has `id`, `phase_type`, `starts_at`), `now: datetime`
- Output: `dict[str, bool]` — `{phase_id: True}` for every in-trip phase whose `starts_at <= now`

`get_trip_travelers` update:
- After loading `all_phases`, call `compute_in_trip_phase_completions` with UTC now
- When computing `_current_phase_id` for each traveler:
  - For **pre-trip** phases: use existing DB-based `completed_by_tt` logic (unchanged)
  - For **in-trip** phases: treat phase as completed if `date_completions[phase_id] == True`
  - `current_phase_id` = first phase (by sort_order) that is NOT completed in either source

### Frontend (`HomeScreen.tsx`)

Determine current **mode** from `tripInfo.start_date`:
```ts
const tripStarted = tripInfo ? new Date(tripInfo.start_date + 'T00:00:00') <= new Date() : false;
```

Filter phases for the progress bar:
```ts
const progressPhases = tripStarted
  ? phases.filter(p => p.phase_type === 'in-trip')
  : phases.filter(p => p.phase_type === 'pre-trip');
```

Pass scoped indexes to `ProgressBar`:
```ts
const currentUserIdx = progressPhases.findIndex(p => p.id === currentUserPhaseId);
const parrotIdx = progressPhases.findIndex(p => p.id === parrotPhaseId);
const totalPhases = progressPhases.length;
```

The game board path (phase list) still renders ALL phases — only the bar changes.

---

## Task 1: Backend — `compute_in_trip_phase_completions` + tests

**Files:**
- Modify: `backend/app/services/trip_service.py`
- Create: `backend/tests/services/test_trip_service.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/services/test_trip_service.py`:

```python
from datetime import UTC, datetime

from app.services.trip_service import compute_in_trip_phase_completions


def _phase(id: str, phase_type: str, starts_at: datetime | None) -> dict:
    return {"id": id, "phase_type": phase_type, "starts_at": starts_at}


def test_in_trip_phase_before_start_not_complete():
    now = datetime(2026, 12, 25, 12, 0, 0, tzinfo=UTC)
    phases = [_phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC))]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": False}


def test_in_trip_phase_on_start_day_complete():
    now = datetime(2026, 12, 26, 8, 0, 0, tzinfo=UTC)
    phases = [_phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC))]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": True}


def test_in_trip_phase_after_start_complete():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [_phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC))]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": True}


def test_pre_trip_phases_excluded():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [
        _phase("pre1", "pre-trip", None),
        _phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC)),
    ]
    result = compute_in_trip_phase_completions(phases, now)
    assert "pre1" not in result
    assert result["p1"] is True


def test_in_trip_phase_no_starts_at_not_complete():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [_phase("p1", "in-trip", None)]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": False}


def test_multiple_days_partial_completion():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [
        _phase("d1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC)),
        _phase("d2", "in-trip", datetime(2026, 12, 27, tzinfo=UTC)),
        _phase("d3", "in-trip", datetime(2026, 12, 28, tzinfo=UTC)),
    ]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"d1": True, "d2": True, "d3": False}
```

- [ ] **Step 2: Run tests — expect ImportError (function not defined yet)**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run pytest tests/services/test_trip_service.py -v 2>&1 | head -20
```
Expected: ImportError or AttributeError on `compute_in_trip_phase_completions`.

- [ ] **Step 3: Add `compute_in_trip_phase_completions` to `trip_service.py`**

Add this function near the top of `backend/app/services/trip_service.py`, after the imports:

```python
from datetime import UTC, datetime as _datetime


def compute_in_trip_phase_completions(
    phases: list[dict], now: _datetime
) -> dict[str, bool]:
    """Return {phase_id: bool} for in-trip phases only.
    A phase is complete if starts_at is set and starts_at <= now.
    Pre-trip phases are not included."""
    result: dict[str, bool] = {}
    for phase in phases:
        if phase["phase_type"] != "in-trip":
            continue
        starts_at = phase["starts_at"]
        if starts_at is None:
            result[phase["id"]] = False
        else:
            if isinstance(starts_at, str):
                starts_at = _datetime.fromisoformat(starts_at)
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=UTC)
            result[phase["id"]] = starts_at <= now
    return result
```

- [ ] **Step 4: Run tests — all must pass**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run pytest tests/services/test_trip_service.py -v
```
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/trip_service.py backend/tests/services/test_trip_service.py
git commit -m "feat: add compute_in_trip_phase_completions to trip_service"
```

---

## Task 2: Backend — update `get_trip_travelers` to merge date-based completions

**Files:**
- Modify: `backend/app/services/trip_service.py` (function `get_trip_travelers`)

- [ ] **Step 1: Locate `get_trip_travelers` in `trip_service.py`**

Read the function. The key section to change is inside `_current_phase_id`:

```python
def _current_phase_id(tt_id: _uuid.UUID) -> str | None:
    if not phases_ordered:
        return None
    max_completed = completed_by_tt.get(tt_id, -1)
    # Próxima fase após a última completada
    for sort_order, pid in phases_ordered:
        if sort_order > max_completed:
            return pid
    # Todas completadas → última fase
    return phases_ordered[-1][1]
```

This only uses DB-based completions. We need to also account for date-based in-trip completions.

- [ ] **Step 2: Update `get_trip_travelers` to use `compute_in_trip_phase_completions`**

Replace the entire body of `get_trip_travelers` with the following (keep the function signature `async def get_trip_travelers(user_id: str, session: AsyncSession) -> dict:` unchanged):

```python
    trip_uuid = await _get_trip_uuid(user_id, session)

    tt_result = await session.execute(
        select(TripTraveler, User)
        .join(User, User.id == TripTraveler.user_id)
        .where(TripTraveler.wetravel_trip_uuid == trip_uuid)
    )
    rows = tt_result.all()

    if not rows:
        return {"travelers": []}

    tt_ids = [tt.id for tt, _ in rows]

    progress_result = await session.execute(
        select(TravelerPhaseProgress, TripPhase)
        .join(TripPhase, TripPhase.id == TravelerPhaseProgress.trip_phase_id)
        .where(
            TravelerPhaseProgress.trip_traveler_id.in_(tt_ids),
            TravelerPhaseProgress.is_completed.is_(True),
        )
        .order_by(TravelerPhaseProgress.trip_traveler_id, TripPhase.sort_order)
    )
    completed_by_tt: dict[_uuid.UUID, int] = {}
    for prog, phase in progress_result.all():
        current = completed_by_tt.get(prog.trip_traveler_id, -1)
        if phase.sort_order > current:
            completed_by_tt[prog.trip_traveler_id] = phase.sort_order

    all_phases_result = await session.execute(
        select(TripPhase)
        .where(TripPhase.wetravel_trip_uuid == trip_uuid, TripPhase.is_visible.is_(True))
        .order_by(TripPhase.sort_order)
    )
    all_phases = all_phases_result.scalars().all()

    phase_dicts = [
        {
            "id": str(p.id),
            "phase_type": p.phase_type,
            "starts_at": p.starts_at,
            "sort_order": p.sort_order,
        }
        for p in all_phases
    ]
    phases_ordered = [(p["sort_order"], p["id"]) for p in phase_dicts]

    now = _datetime.now(UTC)
    date_completions = compute_in_trip_phase_completions(phase_dicts, now)

    # Build a set of phase IDs that are completed (DB or date-based)
    db_completed_ids: dict[_uuid.UUID, set[str]] = {}
    for prog, phase in (await session.execute(
        select(TravelerPhaseProgress, TripPhase)
        .join(TripPhase, TripPhase.id == TravelerPhaseProgress.trip_phase_id)
        .where(
            TravelerPhaseProgress.trip_traveler_id.in_(tt_ids),
            TravelerPhaseProgress.is_completed.is_(True),
        )
    )).all():
        db_completed_ids.setdefault(prog.trip_traveler_id, set()).add(str(prog.trip_phase_id))

    def _current_phase_id(tt_id: _uuid.UUID) -> str | None:
        if not phases_ordered:
            return None
        tt_db_done = db_completed_ids.get(tt_id, set())
        for sort_order, pid in phases_ordered:
            is_done = (pid in tt_db_done) or date_completions.get(pid, False)
            if not is_done:
                return pid
        return phases_ordered[-1][1]

    travelers = []
    for tt, user in rows:
        travelers.append({
            "id": str(user.id),
            "name": user.full_name,
            "phone": user.phone,
            "current_phase_id": _current_phase_id(tt.id),
        })

    return {"travelers": travelers}
```

Note: this re-executes the progress query twice. That's fine for now (small tables, correctness over premature optimization).

- [ ] **Step 3: Verify no syntax errors**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run python -c "from app.services.trip_service import get_trip_travelers"
```
Expected: no output.

- [ ] **Step 4: Run existing tests to check nothing broke**

```bash
poetry run pytest tests/services/test_trip_service.py tests/services/test_checklist_service.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/trip_service.py
git commit -m "feat: merge date-based in-trip completions into get_trip_travelers"
```

---

## Task 3: Backend — `reset_traveler_progress.py` script

**Files:**
- Create: `backend/scripts/reset_traveler_progress.py`

- [ ] **Step 1: Create the script**

Create `backend/scripts/reset_traveler_progress.py`:

```python
"""
Delete all traveler progress (checklist + phase) for a given trip.

Run this ~1 week before trip departure to clear pre-trip progress
so the in-trip phase begins fresh.

Usage:
  cd backend
  poetry run python scripts/reset_traveler_progress.py --trip-uuid gsb-nye-2026

  # Dry run (shows what would be deleted without deleting):
  poetry run python scripts/reset_traveler_progress.py --trip-uuid gsb-nye-2026 --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/parrot_trips",
)
PG_URL = (
    DATABASE_URL
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("postgresql+psycopg2://", "postgresql://")
)


async def reset(trip_uuid: str, dry_run: bool) -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        tt_rows = await conn.fetch(
            "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
        )
        if not tt_rows:
            print(f"No travelers found for trip '{trip_uuid}'.")
            return

        tt_ids = [str(r["id"]) for r in tt_rows]

        checklist_count = await conn.fetchval(
            "SELECT COUNT(*) FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
            tt_ids,
        )
        phase_count = await conn.fetchval(
            "SELECT COUNT(*) FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
            tt_ids,
        )

        print(f"Trip '{trip_uuid}': {len(tt_ids)} traveler(s)")
        print(f"  traveler_checklist_progress rows : {checklist_count}")
        print(f"  traveler_phase_progress rows     : {phase_count}")

        if dry_run:
            print("\nDry run — nothing deleted.")
            return

        confirm = input("\nProceed with deletion? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        async with conn.transaction():
            await conn.execute(
                "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                tt_ids,
            )
            await conn.execute(
                "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                tt_ids,
            )

        print(f"\nDeleted {checklist_count} checklist + {phase_count} phase progress rows.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset traveler progress for a trip")
    parser.add_argument("--trip-uuid", required=True, help="WeTravel trip UUID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()
    asyncio.run(reset(args.trip_uuid, args.dry_run))
```

- [ ] **Step 2: Verify no syntax errors**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run python -c "import scripts.reset_traveler_progress"
```
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/reset_traveler_progress.py
git commit -m "feat: add reset_traveler_progress.py script"
```

---

## Task 4: Frontend — split progress bar by mode

**Files:**
- Modify: `frontend/src/features/trip/pages/HomeScreen.tsx`

The only change is how `totalPhases`, `currentUserIdx`, and `parrotIdx` are computed before being passed to `<ProgressBar>`. The game board path (full phase list) does NOT change.

- [ ] **Step 1: Update `HomeScreen.tsx`**

Find this block in `HomeScreen.tsx` (around lines 69-73):

```typescript
  const currentUserPhaseId = travelers.find(t => t.id === user?.userId)?.current_phase_id ?? null;
  const parrotPhaseId = computeParrotPhaseId(phases);
  const currentUserIdx = phases.findIndex(p => p.id === currentUserPhaseId);
  const parrotIdx = phases.findIndex(p => p.id === parrotPhaseId);
  const totalPhases = phases.length;
```

Replace it with:

```typescript
  const currentUserPhaseId = travelers.find(t => t.id === user?.userId)?.current_phase_id ?? null;
  const parrotPhaseId = computeParrotPhaseId(phases);

  const tripStarted = tripInfo
    ? new Date(tripInfo.start_date + 'T00:00:00') <= new Date()
    : false;

  const progressPhases = tripStarted
    ? phases.filter(p => p.phase_type === 'in-trip')
    : phases.filter(p => p.phase_type === 'pre-trip');

  const currentUserIdx = progressPhases.findIndex(p => p.id === currentUserPhaseId);
  const parrotIdx = progressPhases.findIndex(p => p.id === parrotPhaseId);
  const totalPhases = progressPhases.length;
```

- [ ] **Step 2: Verify TypeScript compiles without errors**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
npm run build 2>&1 | tail -20
```
Expected: build succeeds with no TypeScript errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/trip/pages/HomeScreen.tsx
git commit -m "feat: scope progress bar to pre-trip or in-trip phases based on trip start date"
```

---

## Self-review

**Spec coverage:**
- ✅ Pre-trip: user drives progress (unchanged DB behaviour)
- ✅ In-trip: date-based auto-completion via `compute_in_trip_phase_completions`
- ✅ Progress bar scoped to current mode (pre or in-trip) on frontend
- ✅ Reset script for the team to run before departure
- ✅ No API shape changes — no frontend API layer changes needed

**Placeholder scan:** None found.

**Type consistency:**
- `compute_in_trip_phase_completions(phases: list[dict], now: datetime) -> dict[str, bool]` — used identically in tests (Task 1) and `get_trip_travelers` (Task 2). ✅
- `phase_dicts` keys `"id"`, `"phase_type"`, `"starts_at"` match what `compute_in_trip_phase_completions` reads. ✅
- Frontend: `progressPhases` is `TripPhase[]`, same type as `phases` — `.findIndex` calls are valid. ✅

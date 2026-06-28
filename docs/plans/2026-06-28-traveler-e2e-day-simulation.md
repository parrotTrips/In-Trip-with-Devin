# Traveler E2E Test And Day Simulation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a plain-language traveler E2E test guide and improve the internal script used to simulate in-trip day progression.

**Architecture:** The traveler app already reads in-trip progress from `trip_phases.starts_at`. Keep day simulation as a backend script that updates those dates in Supabase. Put the operational test guide under `tests_documentation` so non-technical readers can follow it.

**Tech Stack:** Python, asyncpg, pytest, Markdown, Google Sheets, Supabase, WeTravel, Netlify deployed frontend, Cloud Run backend.

---

### Task 1: Add Script Date Helper Tests

**Files:**
- Create: `backend/tests/scripts/test_simulate_trip_day.py`
- Modify: `backend/scripts/simulate_trip_day.py`

**Step 1: Write failing tests**

Add tests for helper functions that do not connect to the database:

- `calculate_simulated_starts_at(day_num, target_day, now)`
- `calculate_reset_starts_at(trip_start, day_num)`
- `validate_target_day(target_day, total_days)`

**Step 2: Run test to verify failure**

Run:

```bash
cd backend
poetry run pytest tests/scripts/test_simulate_trip_day.py -q
```

Expected: fail because the helper functions do not exist yet.

**Step 3: Implement helpers**

Add the helper functions to `backend/scripts/simulate_trip_day.py`, then update `simulate()` and `reset_dates()` to use them.

**Step 4: Run tests**

Run:

```bash
cd backend
poetry run pytest tests/scripts/test_simulate_trip_day.py -q
```

Expected: pass.

### Task 2: Improve Reset Logic

**Files:**
- Modify: `backend/scripts/simulate_trip_day.py`

**Step 1: Update reset query**

Read `wetravel_trips.start_date` for the trip UUID.

**Step 2: Reset from trip start date**

For in-trip phase day 1, set `starts_at = start_date`. For day 2, set `starts_at = start_date + 1 day`, and so on.

**Step 3: Fail clearly when start date is missing**

If `wetravel_trips.start_date` is missing, print a clear error and stop without changing dates.

### Task 3: Create Traveler E2E Documentation

**Files:**
- Create: `tests_documentation/traveler_e2e_test_plan.md`

**Step 1: Write baby-step guide**

Cover the full traveler flow:

- WeTravel trip creation;
- traveler purchase simulation;
- spreadsheet content;
- import into Supabase;
- deployed app login;
- pre-trip app validation;
- start trip;
- simulate in-trip day progression;
- in-trip validation;
- issue logging.

**Step 2: Add checkpoints after each major step**

Each step should include "o que conferir" and "o que anotar se der errado".

### Task 4: Verify

**Files:**
- Test: `backend/tests/scripts/test_simulate_trip_day.py`

**Step 1: Run focused backend test**

```bash
cd backend
poetry run pytest tests/scripts/test_simulate_trip_day.py -q
```

**Step 2: Check git diff**

```bash
git diff -- backend/scripts/simulate_trip_day.py backend/tests/scripts/test_simulate_trip_day.py tests_documentation/traveler_e2e_test_plan.md docs/plans/2026-06-28-traveler-e2e-day-simulation-design.md docs/plans/2026-06-28-traveler-e2e-day-simulation.md
```


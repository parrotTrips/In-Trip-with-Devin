# Staff as Travelers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ensure every staff member imported from the Staff sheet is also linked as a traveler for the same trip.

**Architecture:** Keep the dual-link model already used by the app: `trip_staff` for staff operations and `trip_travelers` for traveler app access. Cover the existing `write_staff` flow with a regression test, make any minimal implementation fix needed, then backfill/import production data for the internal Parrot trip.

**Tech Stack:** Python, asyncpg-style connection abstraction, pytest, Supabase/Postgres.

---

### Task 1: Regression Test

**Files:**
- Modify: `backend/tests/scripts/test_import_staff_content.py`

**Step 1: Write the failing test**

Add a test that calls `write_staff` with one staff member and asserts an `INSERT INTO trip_travelers` call was issued with that staff user's ID and target trip UUID.

**Step 2: Run the focused test**

Run:

```bash
cd backend
poetry run pytest tests/scripts/test_import_staff_content.py::test_write_staff_links_staff_user_as_trip_traveler -q
```

Expected before a valid implementation: fail because the traveler link is not created or not asserted.

**Step 3: Implement minimal fix if needed**

If the test fails against production code, update `scripts/import_staff_content.py::write_staff` so each staff member gets an idempotent `trip_travelers` row for the same `trip_uuid`.

**Step 4: Run import staff tests**

Run:

```bash
cd backend
poetry run pytest tests/scripts/test_import_staff_content.py -q
```

Expected: pass.

### Task 2: Production Backfill

**Files:**
- No code files.

**Step 1: Run the Staff import/backfill for `TEST-2026-FULL`**

Use production environment variables and execute the existing admin import or equivalent idempotent SQL to ensure every `trip_staff` row has a matching `trip_travelers` row.

**Step 2: Verify Gabriel**

Query production for `+5516993903965` and confirm both:

- `trip_staff.wetravel_trip_uuid = 'TEST-2026-FULL'`
- `trip_travelers.wetravel_trip_uuid = 'TEST-2026-FULL'`

**Step 3: Report outcome**

Summarize the regression coverage, production repair count, and Gabriel's final state.

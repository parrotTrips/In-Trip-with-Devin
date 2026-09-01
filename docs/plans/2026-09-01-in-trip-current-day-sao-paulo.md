# In-Trip Current Day Sao Paulo Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Compute traveler `current_phase_id` from the current in-trip day in Sao Paulo time once a trip is in-trip.

**Architecture:** Extract pure helper functions in `backend/app/services/trip_service.py` so date behavior can be unit-tested without database setup. `get_trip_travelers` will fetch trip settings and delegate current phase calculation to the helper.

**Tech Stack:** Python 3.12, standard-library `zoneinfo`, SQLAlchemy async service layer, pytest.

---

### Task 1: Add Current Phase Helper Tests

**Files:**
- Modify: `backend/tests/services/test_trip_service.py`

**Step 1: Write the failing tests**

Add tests importing `compute_current_phase_id` from `app.services.trip_service`.

Cover:
- `trip_mode="in-trip"` at `2026-12-26 23:59 America/Sao_Paulo` returns Day 1;
- `trip_mode="in-trip"` at `2026-12-27 00:00 America/Sao_Paulo` returns Day 2;
- `trip_mode="pre-trip"` still returns the first incomplete pre-trip phase.

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/services/test_trip_service.py -q`

Expected: FAIL because `compute_current_phase_id` does not exist.

### Task 2: Implement Sao Paulo In-Trip Calculation

**Files:**
- Modify: `backend/app/services/trip_service.py`

**Step 1: Add helper implementation**

Add:
- `SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")`;
- `_phase_local_date(phase, timezone)`;
- `compute_current_phase_id(phases, completed_phase_ids, trip_mode, now, timezone=SAO_PAULO_TZ)`.

For `in-trip`, filter visible ordered phases to `phase_type == "in-trip"` and select the latest phase whose `starts_at` local date is less than or equal to `now` local date. If none qualify, return the first in-trip phase.

For `pre-trip`, preserve the existing progress-driven logic.

**Step 2: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/services/test_trip_service.py -q`

Expected: PASS.

### Task 3: Wire Helper Into Traveler Response

**Files:**
- Modify: `backend/app/services/trip_service.py`
- Test: `backend/tests/integration/test_trip_routes.py`

**Step 1: Use trip settings in `get_trip_travelers`**

Fetch `_get_trip_settings(trip_uuid, session)` and call `compute_current_phase_id` for each traveler instead of the nested `_current_phase_id`.

**Step 2: Run integration and service tests**

Run: `cd backend && poetry run pytest tests/services/test_trip_service.py tests/integration/test_trip_routes.py -q`

Expected: PASS.

# Pending and Wrap-up Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show Pending only on the traveler's current incomplete pre-trip phase and publish a default Trip Wrap-up for every trip in production and homologation.

**Architecture:** Keep phase selection in the backend and render badges from `current_phase_id` plus completion state. Seed missing Wrap-ups with the existing console template in an idempotent transaction per environment.

**Tech Stack:** React, TypeScript, Vitest, FastAPI, SQLAlchemy, PostgreSQL, Pytest, Netlify, Google Cloud Run.

---

### Task 1: Traveler Pending badge

**Files:**
- Modify: `frontend/src/features/trip/HomeScreen.test.tsx`
- Modify: `frontend/src/features/trip/pages/HomeScreen.tsx`

1. Change the regression test to expect Pending only on the current incomplete pre-trip phase, including while the trip is still pre-trip.
2. Run the focused test and confirm it fails because the current implementation requires in-trip mode.
3. Change `isPending` to require `isPreTrip`, `isCurrent`, and `!isPast`.
4. Run the focused test and confirm it passes.

### Task 2: Staff pending count before departure

**Files:**
- Modify: `backend/tests/services/test_trip_progress.py`
- Modify: `backend/app/services/trip_service.py`

1. Add a regression test proving incomplete pre-trip phases are counted while the trip mode is pre-trip.
2. Run the focused test and confirm it fails with a zero count.
3. Remove the in-trip-only guard from `pending_pre_trip`.
4. Run the focused backend tests and confirm they pass.

### Task 3: Publish Wrap-ups in both databases

**Files:**
- Create: `backend/scripts/ensure_trip_wrap_ups.py`
- Test: `backend/tests/scripts/test_ensure_trip_wrap_ups.py`

1. Add tests for creating and publishing missing Wrap-ups and preserving existing ones.
2. Run them and confirm failure before implementation.
3. Implement the idempotent database operation using the existing template constants.
4. Run the script in production and homologation.
5. Query both databases to verify every trip has exactly one visible post-trip phase.

### Task 4: Verify and deploy

1. Run the complete frontend test suite and production build.
2. Run the complete backend test suite.
3. Commit and push the shared commit to `homologacao` and `main`.
4. Deploy frontend and backend to homologation and production.
5. Verify health endpoints and deployed assets.

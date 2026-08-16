# In-App Feedback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the external feedback form with an in-app editable feedback field stored once per traveler per trip.

**Architecture:** Store feedback in a new `traveler_app_feedback` table keyed by `trip_traveler_id`, so the active traveler can create or update their own feedback for the active trip. Expose `GET /me/app-feedback` and `PUT /me/app-feedback`, then render a textarea and save button inside the existing `Information > Feedback` section.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, PostgreSQL, React, Vitest, MSW.

---

### Task 1: Backend Storage And API

**Files:**
- Create: `backend/alembic/versions/20260816_0022_add_traveler_app_feedback.py`
- Modify: `backend/app/db/models/trip.py`
- Modify: `backend/app/routers/trip.py`
- Test: `backend/tests/integration/test_trip_routes.py`

**Steps:**
1. Write failing integration tests for `GET /me/app-feedback` returning empty feedback and `PUT /me/app-feedback` upserting text for the authenticated traveler.
2. Run the targeted backend test and confirm it fails because the endpoints do not exist.
3. Add the model and Alembic migration with a unique constraint on `trip_traveler_id`.
4. Add helper resolution for the active `TripTraveler`, then implement GET and PUT routes.
5. Re-run the targeted backend test until it passes.

### Task 2: Frontend Feedback Form

**Files:**
- Modify: `frontend/src/features/trip/services/trip-api.ts`
- Modify: `frontend/src/features/team/pages/InformationScreen.tsx`
- Test: `frontend/src/features/team/InformationScreen.test.tsx`

**Steps:**
1. Write a failing test that opens Feedback, sees saved text, edits it, submits, and verifies the PUT payload.
2. Run the targeted frontend test and confirm it fails because the form is not present.
3. Add API helpers for get/update app feedback.
4. Replace the Google Forms link block with textarea, save state, and success/error messaging.
5. Re-run the targeted frontend test until it passes.

### Task 3: Verification

**Steps:**
1. Run backend targeted tests for trip feedback.
2. Run frontend targeted tests for Information/Profile/Recommendations because those screens currently have related local edits.
3. Run frontend build.
4. Report any unrelated pre-existing dirty files separately.

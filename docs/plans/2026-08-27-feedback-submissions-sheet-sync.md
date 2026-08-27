# Feedback Submissions Sheet Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert traveler app feedback into append-only Supabase submissions and add a manual Google Sheets import for operations.

**Architecture:** Supabase is the source of truth. Traveler feedback uses a new `POST /me/app-feedback` create-only flow, while an admin endpoint reads feedbacks for a trip and rewrites a `Feedbacks` tab in the existing trip content spreadsheet on demand.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, PostgreSQL/Supabase, Google Sheets API helpers in `admin_service`, Google Apps Script, React, Vitest/MSW, pytest.

---

### Task 1: Backend Feedback Storage Becomes Append-Only

**Files:**
- Create: `backend/alembic/versions/20260827_0024_allow_multiple_traveler_app_feedback.py`
- Modify: `backend/app/db/models/trip.py`
- Modify: `backend/app/routers/trip.py`
- Test: `backend/tests/integration/test_trip_routes.py`

**Steps:**
1. Update the existing feedback integration test so two sends by the same traveler use `POST /me/app-feedback` and expect two rows in `traveler_app_feedback`.
2. Run `cd backend && poetry run pytest tests/integration/test_trip_routes.py::test_post_my_app_feedback_creates_multiple_feedbacks_per_traveler -q` and confirm it fails because `POST` does not exist or the unique constraint/model still enforces one row.
3. Add an Alembic migration that drops `uq_traveler_app_feedback_trip_traveler_id`.
4. Remove `UniqueConstraint("trip_traveler_id")` from `TravelerAppFeedback`.
5. Replace the `PUT /me/app-feedback` route with `POST /me/app-feedback` that creates a new `TravelerAppFeedback` row every time.
6. Return `{ "id": "...", "feedback": "...", "created_at": "..." }`.
7. Re-run the targeted test and confirm it passes.

### Task 2: Admin Feedback Sheet Sync

**Files:**
- Modify: `backend/app/services/admin_service.py`
- Modify: `backend/app/routers/admin.py`
- Test: `backend/tests/services/test_admin_service.py` or `backend/tests/integration/test_staff_routes.py` if existing admin test patterns fit better.

**Steps:**
1. Write a failing test that seeds one trip with two feedback rows, calls the admin sync helper with a fake Sheets service, and asserts a `Feedbacks` tab receives headers plus two rows.
2. Run the focused test and confirm it fails because the sync helper does not exist.
3. Add `admin_sync_feedback_to_sheet(trip_uuid: str)` to `admin_service`.
4. Query `TravelerAppFeedback`, `TripTraveler`, and `User` for the selected trip, ordered by `created_at`.
5. Use the existing Google Sheets service/config helpers in `admin_service` to create or clear the `Feedbacks` tab and write headers and rows.
6. Add `POST /admin/trips/sync-feedback-to-sheet` in `admin.py`.
7. Re-run the focused backend test and confirm it passes.

### Task 3: Google Apps Script Menu

**Files:**
- Modify: `google-apps-script/Code.gs`
- Test: `backend/tests/scripts/test_google_apps_script_labels.py`

**Steps:**
1. Add a failing test assertion that `Code.gs` contains `Import Feedbacks from App` and calls `/admin/trips/sync-feedback-to-sheet`.
2. Run `cd backend && poetry run pytest tests/scripts/test_google_apps_script_labels.py -q` and confirm it fails.
3. Add a menu item `💬 Import Feedbacks from App`.
4. Add `importFeedbacks()` that prompts for a trip and calls `/admin/trips/sync-feedback-to-sheet`.
5. Re-run the Apps Script label test and confirm it passes.

### Task 4: Frontend Send-Only Feedback

**Files:**
- Modify: `frontend/src/features/trip/services/trip-api.ts`
- Modify: `frontend/src/features/team/pages/InformationScreen.tsx`
- Test: `frontend/src/features/team/InformationScreen.test.tsx`

**Steps:**
1. Update the feedback test so it does not mock `GET /me/app-feedback`, expects a `POST /me/app-feedback` payload, and expects the textarea to clear after success.
2. Run `cd frontend && npm test -- InformationScreen.test.tsx --run` and confirm it fails.
3. Replace `updateMyAppFeedback` with `sendMyAppFeedback` using `POST`.
4. Stop calling `getMyAppFeedback()` from `InformationScreen`.
5. On successful send, clear the textarea, show `Feedback sent`, and keep PostHog capture.
6. Re-run the focused frontend test and confirm it passes.

### Task 5: Verification

**Files:**
- No new source files expected.

**Steps:**
1. Run `cd backend && poetry run pytest tests/integration/test_trip_routes.py tests/scripts/test_google_apps_script_labels.py -q`.
2. Run the focused admin service test added in Task 2.
3. Run `cd frontend && npm test -- InformationScreen.test.tsx --run`.
4. Run `cd frontend && npm run build`.
5. Check `git status --short` and report unrelated pre-existing dirty files separately.

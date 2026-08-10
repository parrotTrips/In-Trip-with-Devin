# Rich Local Recommendations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild local recommendations as a dedicated database-backed page with the richer filters and card layout from the template branch.

**Architecture:** The Trip Content Google Sheet remains the primary authoring source. Backend import stores rich recommendation metadata in `trip_recommendations`, `/me/recommendations` exposes it, and the frontend renders `/recommendations` with filter chips and card fallbacks for older rows.

**Tech Stack:** FastAPI, SQLAlchemy models, Alembic, asyncpg import scripts, Google Apps Script importer, React, React Router, Vitest/Testing Library, Tailwind.

---

### Task 1: Backend Contract And Import

**Files:**
- Modify: `backend/alembic/versions/*_add_rich_recommendation_fields.py`
- Modify: `backend/app/db/models/trip.py`
- Modify: `backend/app/routers/trip.py`
- Modify: `backend/app/services/admin_service.py`
- Modify: `backend/scripts/import_trip_content.py`
- Modify: `google-apps-script/Code.gs`

**Steps:**
1. Add a failing backend/import test or targeted assertion for the new recommendation fields.
2. Add nullable columns: `category`, `neighborhood`, `location`, `highlight`, `price_range`, `rating`, `map_url`, `emoji`.
3. Update the ORM model and `/me/recommendations` response.
4. Update import code to read new sheet columns while preserving compatibility with existing sheets.
5. Update Google Apps Script sheet metadata/help text for the richer columns.
6. Run targeted backend tests or syntax checks.

### Task 2: Frontend Route And Data Type

**Files:**
- Modify: `frontend/src/features/trip/services/trip-api.ts`
- Create: `frontend/src/features/recommendations/pages/RecommendationsScreen.tsx`
- Create: `frontend/src/features/recommendations/RecommendationsScreen.test.tsx`
- Modify: `frontend/src/app/router.tsx`

**Steps:**
1. Add a failing frontend test proving `/recommendations` renders fetched recommendations and filters them.
2. Extend the `Recommendation` type with the rich nullable fields.
3. Build the dedicated page from the template layout using real API data.
4. Add route `/recommendations`.
5. Run targeted frontend tests.

### Task 3: Information Screen Integration

**Files:**
- Modify: `frontend/src/features/team/pages/InformationScreen.tsx`
- Modify/Test: existing information screen tests if present.

**Steps:**
1. Replace the embedded `Local Tips` list with a clear navigation row/link to `/recommendations`.
2. Keep `Information` focused on team, emergency contacts, FAQ, feedback, and cancellation policy.
3. Run targeted tests/build.

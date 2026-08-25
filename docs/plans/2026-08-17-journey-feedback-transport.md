# Journey Feedback Transport Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show activity locations in Journey, make feedback read as a send action, prioritize transportation recommendations, and add transport WhatsApp useful links for the wedding trip.

**Architecture:** Reuse existing data fields and routes. `trip_activities.address` already exists in the backend and sheet import path, so the API type/UI should consume it. Feedback remains persisted through the existing app-feedback endpoint, while copy changes to send language. Transport links are seeded through the existing Links tab and imported into pre-trip phases.

**Tech Stack:** React, TypeScript, Vite/Vitest, Python seed scripts, Google Sheets importer, Supabase/Postgres.

---

### Task 1: Journey Activity Address UI

**Files:**
- Modify: `frontend/src/features/trip/services/trip-api.ts`
- Modify: `frontend/src/features/trip/pages/DayDetails.tsx`
- Test: `frontend/src/features/trip/DayDetails.test.tsx`

**Steps:**
1. Add a failing frontend test that renders an activity with `address` and expects the address text on the Journey day detail card.
2. Run `npm test -- DayDetails.test.tsx --runInBand` or the repo's Vitest equivalent and confirm the test fails because the address is not rendered or typed.
3. Add `address: string | null` to the `Activity` TypeScript interface.
4. Render `activity.address` in `ActivityCard` with a `MapPin` icon, visible in the card.
5. Re-run the DayDetails test and confirm it passes.

### Task 2: Feedback Send Copy

**Files:**
- Modify: `frontend/src/features/team/pages/InformationScreen.tsx`
- Test: `frontend/src/features/team/InformationScreen.test.tsx`

**Steps:**
1. Update the existing feedback test to expect `Send Feedback`, `Sending...`, and `Feedback sent`.
2. Run the focused InformationScreen test and confirm it fails on the old save copy.
3. Replace save-oriented labels/messages with send-oriented copy while preserving the existing endpoint.
4. Re-run the focused InformationScreen test and confirm it passes.

### Task 3: Transportation Filter Priority

**Files:**
- Modify: `frontend/src/features/recommendations/pages/RecommendationsScreen.tsx`
- Test: `frontend/src/features/recommendations/RecommendationsScreen.test.tsx`

**Steps:**
1. Add or update a recommendations test so categories returned out of order still render with `Transportation` immediately after `All`.
2. Run the focused recommendations test and confirm it fails.
3. Sort category filter options with `Transportation` first after `All`, preserving the existing order for other categories.
4. Re-run the focused recommendations test and confirm it passes.

### Task 4: Wedding Transport Useful Links

**Files:**
- Modify: `backend/scripts/seed_casamento_garapha_content.py`
- Test: `backend/tests/scripts/test_seed_casamento_garapha_content.py`

**Steps:**
1. Add a failing seed test asserting the Links tab includes WhatsApp transport links under `logistica_de_viagem`.
2. Run the focused backend seed test and confirm it fails.
3. Add `wa.me/55...` links for the transport providers already in Local Recommendations.
4. Re-run the backend seed test and confirm it passes.

### Task 5: Import, Verify, Commit, Deploy

**Files:**
- No new source files expected.

**Steps:**
1. Run relevant frontend and backend tests.
2. Run `poetry run python scripts/seed_casamento_garapha_content.py --execute --import-db` from `backend`.
3. Query Supabase or use the app/API to confirm the links and activity addresses are present.
4. Commit all changes except `docs/data-requests/20260806-data-request-casamento-garapha.md`.
5. Push `main`.
6. Deploy frontend because UI code changed; deploy backend only if backend runtime code changed.

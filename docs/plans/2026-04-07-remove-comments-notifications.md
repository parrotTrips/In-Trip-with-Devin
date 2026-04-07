# Remove Comments and Notifications Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove comments and notifications from the active schema docs, DB artifacts, backend APIs, frontend UI, mock data, and tests.

**Architecture:** This is a full feature-removal pass. The implementation first removes the concepts from the canonical database model and visual artifacts, then removes the backend support code, then strips the frontend screens and API calls, and finally updates tests so the active suite only covers the remaining product scope.

**Tech Stack:** Markdown documentation, DBML, dbdiagram JSON, Python/FastAPI, TypeScript/React, Vitest

---

### Task 1: Remove comments and notifications from the active model docs

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/02-erd-conceitual.md`
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
- Modify: `MODELO_BANCO_DE_DADOS/04-vertabelo.md`
- Modify: `MODELO_BANCO_DE_DADOS/05-cardinalidades.md`
- Modify: `docs/db/parrot-trips-erd.dbml`
- Modify: `docs/db/parrot-trips-erd.dbdiagram`
- Modify: `docs/plans/2026-04-06-dbml-erd.md`
- Modify: `docs/plans/2026-04-06-traveler-only-domain-design.md`
- Modify: `docs/plans/2026-04-06-simplify-trip-travelers-design.md`

**Step 1: Remove the entities from the docs and DBML**

Delete `phase_comments` and `notifications` sections/tables from the active model docs and DBML artifact.

**Step 2: Remove related relationships and diagram references**

Delete cardinality references and dbdiagram nodes/edges for those two entities.

**Step 3: Remove stale plan/design references**

Update plan/design docs that still mention `notifications`, `comment`, or `phase_comments` as part of the active scope.

**Step 4: Verify the model artifacts**

Run: `rg -n 'phase_comments|notifications|PhaseComment|Notification' MODELO_BANCO_DE_DADOS docs/db docs/plans/2026-04-06-dbml-erd.md docs/plans/2026-04-06-traveler-only-domain-design.md docs/plans/2026-04-06-simplify-trip-travelers-design.md`
Expected: no stale active references remain.

### Task 2: Remove backend support code

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/db/database.py`
- Delete: `backend/app/routers/comments.py`
- Delete: `backend/app/routers/notifications.py`
- Delete: `backend/app/services/comment_service.py`
- Delete: `backend/app/services/notification_service.py`
- Delete: `backend/app/schemas/comments.py`
- Delete: `backend/app/schemas/notifications.py`

**Step 1: Remove router registration**

Delete the comment/notification router imports and `include_router` calls from `backend/app/main.py`.

**Step 2: Remove database tables**

Delete the `comments` and `notifications` schema statements from `backend/app/db/database.py`.

**Step 3: Delete feature-specific modules**

Remove the comment and notification routers, services, and schemas.

**Step 4: Verify the backend**

Run: `rg -n 'comments|notifications|comment_service|notification_service' backend/app`
Expected: no active feature references remain.

### Task 3: Remove frontend comments and notifications

**Files:**
- Modify: `frontend/src/data/tripData.ts`
- Modify: `frontend/src/features/trip/pages/PhaseDetails.tsx`
- Modify: `frontend/src/features/trip/pages/DayDetails.tsx`
- Modify: `frontend/src/features/trip/services/trip-api.ts`
- Modify: `frontend/src/shared/components/TopBar.tsx`
- Modify: `frontend/src/app/router.tsx`
- Delete: `frontend/src/features/notifications/pages/NotificationsScreen.tsx`
- Delete: `frontend/src/features/notifications/services/notifications-api.ts`

**Step 1: Remove mock/comment types**

Delete the `Comment` interface, remove `comments` from phase mocks, and strip comments-related state and API usage from the trip detail screens.

**Step 2: Remove notifications UI**

Delete the notifications screen and API client, remove the notifications route, and simplify the top bar so it no longer shows a bell or unread badge.

**Step 3: Verify the frontend**

Run: `rg -n 'comments|notifications|addComment|getComments|getUnreadCount|Bell|MessageSquare|Send' frontend/src`
Expected: no stale feature references remain in active frontend code.

### Task 4: Update tests

**Files:**
- Modify: `frontend/src/app/App.test.tsx`
- Modify: `frontend/src/shared/components/TopBar.test.tsx`
- Modify: `frontend/src/features/trip/PhaseDetails.test.tsx`
- Modify: `frontend/src/features/trip/DayDetails.test.tsx`
- Delete: `frontend/src/features/notifications/NotificationsScreen.test.tsx`

**Step 1: Remove notification-specific expectations**

Adjust app/top bar tests so they no longer mock unread-count endpoints or expect notification UI.

**Step 2: Remove comment-specific expectations**

Adjust trip detail tests so they no longer mock or assert comment loading.

**Step 3: Delete notifications screen test**

Remove the dedicated notifications test file.

**Step 4: Verify the test files**

Run: `rg -n 'comments|notifications' frontend/src/app/App.test.tsx frontend/src/shared/components/TopBar.test.tsx frontend/src/features/trip/PhaseDetails.test.tsx frontend/src/features/trip/DayDetails.test.tsx frontend/src/features/notifications`
Expected: no active references remain after the test cleanup.

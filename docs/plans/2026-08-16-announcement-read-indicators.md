# Announcement Read Indicators Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Persist per-traveler announcement read state and show an unread indicator on the notification bell until each message is expanded.

**Architecture:** Add a normalized read-receipt table keyed by announcement and user. Traveler announcement APIs return per-message `is_read` and aggregate `unread_count`; expanding an unread card calls an idempotent mark-read endpoint. The header fetches unread state through the existing trip API layer and renders a small badge.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, PostgreSQL, React, TypeScript, Vite, Vitest, Testing Library, MSW.

---

### Task 1: Backend Read Model And Migration

**Files:**
- Create: `backend/alembic/versions/20260816_0021_add_trip_announcement_reads.py`
- Modify: `backend/app/db/models/staff.py`
- Modify: `backend/app/db/models/__init__.py`

**Step 1: Write the failing import/schema check**

Add a minimal assertion to an existing backend model or route test that imports `TripAnnouncementRead` from `app.db.models.staff`.

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/integration/test_trip_routes.py -q`

Expected: FAIL because `TripAnnouncementRead` does not exist.

**Step 3: Write minimal implementation**

Add `TripAnnouncementRead` with `announcement_id`, `user_id`, and `read_at`, plus unique and lookup indexes. Add the Alembic migration for the same table.

**Step 4: Run migration-backed test**

Run: `cd backend && poetry run pytest tests/integration/test_trip_routes.py -q`

Expected: PASS for existing route tests after Alembic creates the table.

**Step 5: Commit**

Run:

```bash
git add backend/alembic/versions/20260816_0021_add_trip_announcement_reads.py backend/app/db/models/staff.py backend/app/db/models/__init__.py backend/tests/integration/test_trip_routes.py
git commit -m "feat: add announcement read model"
```

### Task 2: Backend Traveler Announcement Read APIs

**Files:**
- Modify: `backend/app/routers/trip.py`
- Test: `backend/tests/integration/test_trip_routes.py`

**Step 1: Write failing tests**

Add tests that seed two announcements for the traveler's trip and assert:

- `GET /me/announcements` returns `is_read: false` and `unread_count: 2`
- `POST /me/announcements/{id}/read` marks only that announcement as read
- repeated mark-read calls keep a single read row
- marking an announcement from another trip returns 404

**Step 2: Run tests to verify failure**

Run: `cd backend && poetry run pytest tests/integration/test_trip_routes.py -q`

Expected: FAIL because the response shape and mark-read endpoint do not exist.

**Step 3: Implement API changes**

Update `GET /me/announcements` to outer join read receipts for `request.state.user_id`, return `is_read`, and compute `unread_count`.

Add `POST /me/announcements/{announcement_id}/read`. Verify the announcement belongs to the authenticated traveler's active trip, insert `TripAnnouncementRead`, handle duplicates idempotently, commit, and return `{ "status": "read", "announcement_id": "..." }`.

**Step 4: Run backend tests**

Run: `cd backend && poetry run pytest tests/integration/test_trip_routes.py -q`

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add backend/app/routers/trip.py backend/tests/integration/test_trip_routes.py
git commit -m "feat: track traveler announcement reads"
```

### Task 3: Frontend API Types

**Files:**
- Modify: `frontend/src/features/trip/services/trip-api.ts`

**Step 1: Update types and functions**

Add `is_read` to `Announcement`, update `getMyAnnouncements()` to return `{ announcements, unread_count }`, and add `markAnnouncementRead(id: string)`.

**Step 2: Run typecheck**

Run: `cd frontend && npm run build`

Expected: any compile errors point to call sites that need the new response shape.

**Step 3: Commit**

Run:

```bash
git add frontend/src/features/trip/services/trip-api.ts
git commit -m "feat: add announcement read api client"
```

### Task 4: Notifications Screen Read-On-Expand

**Files:**
- Modify: `frontend/src/features/notifications/pages/NotificationsScreen.tsx`
- Test: `frontend/src/features/notifications/NotificationsScreen.test.tsx`

**Step 1: Write failing UI tests**

Test that unread announcements render with an unread indicator and that clicking an unread collapsed card calls `POST /me/announcements/{id}/read`.

**Step 2: Run tests to verify failure**

Run: `cd frontend && npm run test -- NotificationsScreen.test.tsx --run`

Expected: FAIL because the screen does not mark announcements read.

**Step 3: Implement read-on-expand**

Keep local `announcements` state with `is_read`. When a card expands and `is_read` is false, call `markAnnouncementRead`, then update that card to `is_read: true`. If the call fails, keep it unread.

**Step 4: Run frontend notification tests**

Run: `cd frontend && npm run test -- NotificationsScreen.test.tsx --run`

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add frontend/src/features/notifications/pages/NotificationsScreen.tsx frontend/src/features/notifications/NotificationsScreen.test.tsx
git commit -m "feat: mark announcements read on expand"
```

### Task 5: Bell Unread Indicator

**Files:**
- Modify: `frontend/src/shared/components/AppHeader.tsx`
- Modify: `frontend/src/shared/components/TopBar.tsx`
- Test: `frontend/src/shared/components/TopBar.test.tsx`
- Test: `frontend/src/shared/components/AppHeader.test.tsx`

**Step 1: Write failing tests**

Test that each header renders a visual unread badge when passed a positive unread count and omits it when the count is zero.

**Step 2: Implement props and badge**

Add optional `unreadNotificationsCount?: number` to both header components and render a small positioned dot on the bell button when the count is greater than zero.

**Step 3: Wire notifications count**

In traveler screens that render the app header, fetch announcement metadata through `getMyAnnouncements()` or pass through state where already loaded. Keep the first implementation simple and avoid app-wide polling.

**Step 4: Run frontend tests**

Run: `cd frontend && npm run test -- TopBar.test.tsx AppHeader.test.tsx --run`

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add frontend/src/shared/components/AppHeader.tsx frontend/src/shared/components/TopBar.tsx frontend/src/shared/components/TopBar.test.tsx frontend/src/shared/components/AppHeader.test.tsx
git commit -m "feat: show unread notification badge"
```

### Task 6: Final Verification

**Files:**
- All files changed by previous tasks

**Step 1: Run backend integration tests**

Run: `cd backend && poetry run pytest tests/integration/test_trip_routes.py tests/integration/test_staff_routes.py -q`

Expected: PASS.

**Step 2: Run frontend tests and build**

Run: `cd frontend && npm run test -- --run`

Expected: PASS.

Run: `cd frontend && npm run build`

Expected: PASS.

**Step 3: Final commit if needed**

Commit any small follow-up fixes with a focused message.

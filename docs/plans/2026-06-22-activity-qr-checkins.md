# Activity QR Check-ins Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build traveler QR identity and staff activity-specific QR check-ins with one check-in per traveler per activity and per-activity counters.

**Architecture:** Add an `activity_checkins` table with a unique `(trip_activity_id, trip_traveler_id)` constraint. Traveler QR codes contain a signed traveler-trip payload. Staff scans happen from a specific activity and call a backend endpoint that validates trip membership, records the authenticated staff user, and returns success or duplicate status.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, asyncpg, React/Vite, Vitest/MSW, QR rendering/scanning library selected during implementation from existing frontend dependencies or a small proven package.

---

### Task 1: Add Activity Check-in Data Model

**Files:**
- Create: `backend/alembic/versions/20260622_0010_add_activity_checkins.py`
- Modify: `backend/app/db/models/staff.py`
- Test: `backend/tests/test_database_setup.py`

**Step 1: Write failing metadata test**

Add a test asserting `activity_checkins` exists with foreign keys to `trip_activities`, `trip_travelers`, and `users`, plus a unique constraint on `trip_activity_id` and `trip_traveler_id`.

Run:

```bash
cd backend
poetry run pytest tests/test_database_setup.py::test_activity_checkins_table_metadata -v
```

Expected: FAIL because the table does not exist.

**Step 2: Add model and migration**

Create model `ActivityCheckin` with:

- `trip_activity_id`
- `trip_traveler_id`
- `scanned_by_user_id`
- `checked_in_at`

Create migration with:

- table creation;
- foreign keys;
- unique constraint;
- useful indexes on `trip_activity_id` and `trip_traveler_id`.

**Step 3: Verify**

Run:

```bash
cd backend
poetry run pytest tests/test_database_setup.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add backend/alembic/versions/20260622_0010_add_activity_checkins.py backend/app/db/models/staff.py backend/tests/test_database_setup.py
git commit -m "feat: add activity checkins table"
```

### Task 2: Add QR Payload Signing

**Files:**
- Create: `backend/app/services/qr_service.py`
- Test: `backend/tests/services/test_qr_service.py`

**Step 1: Write failing tests**

Cover:

- signed payload can be decoded;
- tampered payload is rejected;
- wrong `type` is rejected.

Run:

```bash
cd backend
poetry run pytest tests/services/test_qr_service.py -v
```

Expected: FAIL because service does not exist.

**Step 2: Implement QR service**

Use `jose.jwt` with existing `JWT_SECRET` initially:

- `create_traveler_qr_payload(trip_traveler_id, trip_uuid)`
- `decode_traveler_qr_payload(token)`

Payload fields:

- `type: traveler_checkin`
- `trip_traveler_id`
- `trip_uuid`

**Step 3: Verify and commit**

```bash
cd backend
poetry run pytest tests/services/test_qr_service.py -v
git add backend/app/services/qr_service.py backend/tests/services/test_qr_service.py
git commit -m "feat: sign traveler QR payloads"
```

### Task 3: Add Traveler QR Endpoint

**Files:**
- Modify: `backend/app/routers/trip.py`
- Test: `backend/tests/integration/test_trip_routes.py`

**Step 1: Write failing integration test**

Seed a traveler in a trip, authenticate, call:

```http
GET /me/qr-code
```

Assert response includes:

- `trip_uuid`
- `trip_traveler_id`
- `qr_payload`

Expected: FAIL with 404.

**Step 2: Implement endpoint**

Resolve authenticated user active trip via `trip_travelers`, sign payload using `qr_service`, return JSON.

**Step 3: Verify and commit**

```bash
cd backend
poetry run pytest tests/integration/test_trip_routes.py -v
git add backend/app/routers/trip.py backend/tests/integration/test_trip_routes.py
git commit -m "feat: expose traveler QR payload"
```

### Task 4: Add Staff Scan Endpoint

**Files:**
- Modify: `backend/app/routers/staff.py`
- Test: `backend/tests/integration/test_staff_routes.py`

**Step 1: Write failing tests**

Cover:

- first scan returns `status: checked_in`;
- duplicate scan returns `status: already_checked_in`;
- duplicate does not insert a second row;
- wrong trip QR returns 400 or 403;
- `scanned_by_user_id` is the authenticated staff user.

Run:

```bash
cd backend
poetry run pytest tests/integration/test_staff_routes.py -v
```

Expected: FAIL because endpoint does not exist.

**Step 2: Implement endpoint**

Add:

```http
POST /me/staff/activities/{activity_id}/checkins/scan
```

Body:

```json
{ "qr_payload": "..." }
```

Behavior:

- decode payload;
- fetch activity and staff active trip;
- fetch trip traveler from payload;
- ensure same `trip_uuid`;
- insert check-in;
- on unique conflict, return duplicate info from existing row.

**Step 3: Verify and commit**

```bash
cd backend
poetry run pytest tests/integration/test_staff_routes.py -v
git add backend/app/routers/staff.py backend/tests/integration/test_staff_routes.py
git commit -m "feat: scan travelers into staff activities"
```

### Task 5: Add Check-in Counters To Staff Trip API

**Files:**
- Modify: `backend/app/routers/staff.py`
- Test: `backend/tests/integration/test_staff_routes.py`
- Modify: `frontend/src/features/staff/services/staff-api.ts`

**Step 1: Write failing backend test**

Seed:

- two travelers in the trip;
- one check-in for one activity.

Assert `GET /me/staff/trip` activity includes:

```json
{
  "checkin_count": 1,
  "traveler_count": 2
}
```

Expected: FAIL because fields are missing.

**Step 2: Implement query**

In staff trip response:

- compute traveler count from `trip_travelers JOIN users WHERE role = 'traveler'`;
- compute check-in count grouped by activity.

**Step 3: Update frontend types**

Add `checkin_count` and `traveler_count` to `StaffActivity`.

**Step 4: Verify and commit**

```bash
cd backend
poetry run pytest tests/integration/test_staff_routes.py -v
cd ../frontend
npm test -- StaffScreen.test.tsx --run
git add backend/app/routers/staff.py backend/tests/integration/test_staff_routes.py frontend/src/features/staff/services/staff-api.ts
git commit -m "feat: return staff activity checkin counters"
```

### Task 6: Add Traveler QR UI

**Files:**
- Modify: `frontend/src/features/trip/services/trip-api.ts`
- Modify: traveler UI screen selected during implementation, likely `frontend/src/features/trip/pages/HomeScreen.tsx` or a new QR component.
- Test: add/update frontend test.

**Step 1: Choose QR rendering package**

Prefer a small maintained package such as `qrcode.react` if no QR renderer exists.

**Step 2: Write failing test**

Mock `/me/qr-code`, render traveler app, assert QR section/tab shows.

**Step 3: Implement UI**

Add `My QR Code` entry in traveler experience. Show:

- QR image;
- traveler name;
- trip title;
- brief instruction to present it to staff.

**Step 4: Verify and commit**

```bash
cd frontend
npm test -- --run
npm run build
git add frontend/src
git commit -m "feat: show traveler QR code"
```

### Task 7: Move Staff Scanner Into Activity Context

**Files:**
- Modify: `frontend/src/features/staff/pages/StaffScreen.tsx`
- Modify: `frontend/src/features/staff/services/staff-api.ts`
- Test: `frontend/src/features/staff/StaffScreen.test.tsx`

**Step 1: Write failing tests**

Assert:

- activity row shows `0 / N checked in`;
- expanded activity has `Scan Travelers` button;
- global `QR Scan` tab is not the primary flow or requires selecting activity.

**Step 2: Implement activity scanner entry**

Inside expanded activity:

- show counter;
- add `Scan Travelers` button;
- scanner modal/screen receives `activity_id`.

**Step 3: Integrate scan endpoint**

Add API function:

```ts
scanActivityTraveler(activityId: string, qrPayload: string)
```

Handle success and duplicate UI states.

**Step 4: Verify and commit**

```bash
cd frontend
npm test -- StaffScreen.test.tsx --run
npm run build
git add frontend/src/features/staff
git commit -m "feat: scan travelers from staff activities"
```

### Task 8: End-to-End Verification

**Files:**
- No required code files unless fixing issues.

**Step 1: Run backend suite**

```bash
cd backend
poetry run pytest -v
```

Expected: PASS.

**Step 2: Run frontend suite and build**

```bash
cd frontend
npm test -- --run
npm run build
```

Expected: PASS.

**Step 3: Apply migration and deploy**

```bash
cd backend
set -a; source .env.production; set +a; poetry run alembic upgrade head
cd ..
make deploy-backend
make deploy-frontend
```

**Step 4: Manual production validation**

Use test trip:

1. Login as traveler.
2. Open `My QR Code`.
3. Login as staff.
4. Open Staff itinerary.
5. Open one activity.
6. Confirm counter starts at expected value.
7. Tap `Scan Travelers`.
8. Scan traveler QR.
9. Confirm counter increments.
10. Scan same QR again.
11. Confirm duplicate message and no counter increment.

**Step 5: Commit any final fixes**

Commit only intentional fixes. Do not include unrelated `roadmap.md`, logs, or `resume.txt`.


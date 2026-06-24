# Controlled Activity QR Governance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add activity participant allowlists and scan audit events so controlled activities can reject unauthorized traveler QR scans.

**Architecture:** The backend keeps `activity_checkins` as the source of successful check-ins. A new `activity_participants` table controls only activities with explicit participant rows, and a new `activity_checkin_scan_events` table records every scan attempt outcome. The Staff Google Sheet gains a `Participantes Atividades` import path that populates `activity_participants`.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, asyncpg, Google Sheets API, Pytest, React staff scanner error display

---

### Task 1: Database models and migration

**Files:**
- Create: `backend/alembic/versions/20260624_0011_add_activity_participants_and_scan_events.py`
- Modify: `backend/app/db/models/staff.py`

**Step 1: Add failing/import tests by referencing new models**

Run existing staff route tests after adding references to `ActivityParticipant` and `ActivityCheckinScanEvent`.

**Step 2: Add migration**

Create `activity_participants` and `activity_checkin_scan_events`, with foreign keys and indexes.

**Step 3: Add SQLAlchemy models**

Add `ActivityParticipant` and `ActivityCheckinScanEvent` to `backend/app/db/models/staff.py`.

**Step 4: Run backend tests**

Run: `poetry run pytest backend/tests/integration/test_staff_routes.py backend/tests/scripts/test_import_staff_content.py`

Expected: PASS after later tasks are complete.

---

### Task 2: Staff Sheet participant import

**Files:**
- Modify: `backend/scripts/import_staff_content.py`
- Modify: `backend/app/services/admin_service.py`
- Modify: `backend/app/routers/admin.py`
- Modify: `backend/tests/scripts/test_import_staff_content.py`

**Step 1: Add parser tests**

Test `parse_activity_participants_tab` with columns:

```text
trip_uuid | dia | atividade_nome | traveler_phone | status
```

**Step 2: Add writer tests**

Use a fake async connection to confirm day, activity, traveler, and membership lookup.

**Step 3: Implement parser and writer**

Resolve day/activity similarly to staff tasks. Delete existing participant rows for the trip and insert fresh allowed rows.

**Step 4: Add admin endpoint**

Expose:

```text
POST /admin/trips/import-activity-participants
```

Expected response:

```json
{"status":"ok","trip_uuid":"TEST-2026-FULL","activity_participants_imported":2}
```

---

### Task 3: Scan validation and audit events

**Files:**
- Modify: `backend/app/routers/staff.py`
- Modify: `backend/tests/integration/test_staff_routes.py`

**Step 1: Add integration tests**

Cover:

- uncontrolled activity still accepts any traveler in the trip;
- controlled activity accepts listed traveler;
- controlled activity rejects unlisted traveler with `403`;
- rejected scan creates an audit event;
- duplicate scan creates an audit event.

**Step 2: Implement event logging helper**

Record scan status, failure reason, resolved activity/traveler IDs when available, staff ID, and a hash of the raw payload.

**Step 3: Implement controlled activity check**

If participant rows exist for the activity, require an `allowed` row for the scanned traveler.

**Step 4: Run integration tests**

Run: `poetry run pytest backend/tests/integration/test_staff_routes.py`

Expected: PASS

---

### Task 4: Verification and deploy

**Files:**
- Backend only unless frontend error copy needs adjustment.

**Step 1: Run targeted tests**

Run:

```bash
poetry run pytest backend/tests/integration/test_staff_routes.py backend/tests/scripts/test_import_staff_content.py
```

Expected: PASS

**Step 2: Run migration locally against production only after tests pass**

Run:

```bash
set -a; source backend/.env.production; set +a; cd backend; poetry run alembic upgrade head
```

Expected: migration applies cleanly.

**Step 3: Deploy backend**

Run the repo's backend deployment command.

**Step 4: Import participants when the sheet tab exists**

Run:

```bash
curl -sS -X POST https://parrot-trips-backend-428743191336.southamerica-east1.run.app/admin/trips/import-activity-participants \
  -H "Content-Type: application/json" \
  -d '{"trip_uuid":"TEST-2026-FULL"}'
```

Expected: response reports imported participant count.


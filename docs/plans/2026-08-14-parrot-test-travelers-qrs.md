# Parrot Test Travelers QR Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Populate `TEST-2026-FULL` with 20 fictitious travelers, align the existing Google Sheets with the Supabase state, and upload one real QR image per traveler to the requested Google Drive folder.

**Architecture:** A single idempotent backend script owns the operation. Supabase is the execution source for traveler IDs because QR payloads require the real `trip_traveler_id`; Google Sheets are updated as aligned operational mirrors; Google Drive stores generated QR PNGs and the local output folder stores audit JSON/CSV.

**Tech Stack:** Python 3.12, asyncpg, Google Sheets API, Google Drive API, python-jose QR payload signing, qrcode/Pillow for PNG generation, pytest.

---

### Task 1: Add Seed Dataset and Tests

**Files:**
- Create: `backend/scripts/seed_parrot_test_travelers.py`
- Create: `backend/tests/scripts/test_seed_parrot_test_travelers.py`

**Steps:**
1. Add a deterministic `TEST_TRAVELERS` dataset with 20 fictitious travelers, unique `+15550102xxx` phones, emails under `example.com`, package/room/add-on data, and profile fields.
2. Add tests proving there are exactly 20 travelers, phone/email uniqueness, no real-looking email domains, and restricted activity allowlists are proper subsets.
3. Run `cd backend && .venv/bin/pytest tests/scripts/test_seed_parrot_test_travelers.py -q`; first run should fail before implementation, then pass.

### Task 2: Implement Supabase Dry-Run and Execute

**Files:**
- Modify: `backend/scripts/seed_parrot_test_travelers.py`

**Steps:**
1. Load `DATABASE_URL` and `JWT_SECRET` from `backend/.env`.
2. On `--dry-run`, report the target trip, existing test users, rows that would be upserted, and dependent rows.
3. On `--execute`, upsert `users`, `trip_travelers`, `traveler_profiles`, `traveler_products`, `wetravel_bookings`, `wetravel_payments`, `wetravel_order_options`, `wetravel_participant_phones`, and selected `activity_participants`.
4. Make the script idempotent by using stable order IDs/participant IDs/entity keys based on the test traveler index.

### Task 3: Align Existing Google Sheets

**Files:**
- Modify: `backend/scripts/seed_parrot_test_travelers.py`

**Sheets:**
- Trip content: `1N1B66s1-K4DDf2_863frmhnpF6LRZB_ww60uax0gKZM`
- Staff content: `1iVv9k45F3dacjYEwR4TsIuGuFtFmVgN3y0ueghvNWiI`

**Steps:**
1. Update `Viagens` rows for `TEST-2026-FULL` in both spreadsheets to `Viagem Interna Parrot`.
2. Update staff spreadsheet rows for `Contatos`, `Staff`, `Tarefas Staff`, and `Participantes Atividades` for `TEST-2026-FULL` from Supabase/script data.
3. Add a traveler audit tab if missing: `Viajantes Teste`, containing names, phones, emails, package, room type, add-ons, `user_id`, `trip_traveler_id`, QR filename, and Drive link.
4. Never write tokens or QR payloads to Sheets.

### Task 4: Generate and Upload QR Images

**Files:**
- Modify: `backend/scripts/seed_parrot_test_travelers.py`

**Drive Folder:**
- `1qXJejeBsUBw7st3ipwJtpppcbwZLXZsE`

**Steps:**
1. Generate signed QR payloads with `create_traveler_qr_payload(trip_traveler_id, "TEST-2026-FULL")`.
2. Render each payload as a PNG.
3. Upload or replace QR PNGs in the target folder using stable filenames: `parrot-test-01-<slug>.png`.
4. Store returned Drive file IDs/links in local audit output and the `Viajantes Teste` sheet.

### Task 5: Verification

**Commands:**
- `cd backend && .venv/bin/pytest tests/scripts/test_seed_parrot_test_travelers.py -q`
- `cd backend && .venv/bin/python scripts/seed_parrot_test_travelers.py --dry-run`
- `cd backend && .venv/bin/python scripts/seed_parrot_test_travelers.py --execute`
- Run final read-only validation against Supabase, Sheets, and Drive.

**Expected final state:**
- 20 fictitious travelers linked to `TEST-2026-FULL`.
- Package/payment profile data visible through the existing profile data path.
- Controlled activities have traveler subsets, not all 20.
- The two existing Sheets have `TEST-2026-FULL` rows aligned with the current trip.
- The Drive folder contains 20 QR PNG files.
- Local audit output exists under `backend/outputs/parrot-test-travelers/`.

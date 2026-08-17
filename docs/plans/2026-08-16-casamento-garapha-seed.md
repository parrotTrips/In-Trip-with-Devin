# Casamento GaRapha Seed Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Seed the `CASAMENTO-GARAPHA-2026` wedding trip with Gabriela and Raphael as travelers, and mirror the minimal rows into the shared Google Sheets audit/reference tabs.

**Architecture:** Add a small standalone script under `backend/scripts` that is idempotent and dry-run by default. Keep the data local to the script, write only the minimal app tables, and update only rows matching this trip UUID in Google Sheets.

**Tech Stack:** Python, asyncpg, python-dotenv, Google Sheets API, existing project virtualenv.

---

### Task 1: Add Script Tests

**Files:**
- Create: `backend/tests/scripts/test_seed_casamento_garapha.py`
- Create: `backend/scripts/seed_casamento_garapha.py`

**Steps:**
1. Write tests for phone normalization, trip rows, traveler audit rows, and dry-run summary.
2. Run `cd backend && .venv/bin/python -m pytest tests/scripts/test_seed_casamento_garapha.py -q`.
3. Verify tests fail because the script does not exist yet.

### Task 2: Implement Dry-Run Data Builder

**Files:**
- Create: `backend/scripts/seed_casamento_garapha.py`

**Steps:**
1. Add constants for trip and traveler data from `20260806 - Data Request Casamento GaRapha.md`.
2. Add helper functions that build Google Sheets row payloads without side effects.
3. Add CLI flags: `--execute`, `--skip-sheets`, `--output-dir`.
4. Run the script without `--execute` and verify it prints planned changes only.

### Task 3: Implement Supabase Writes

**Files:**
- Modify: `backend/scripts/seed_casamento_garapha.py`

**Steps:**
1. Load `DATABASE_URL` from `backend/.env`.
2. Upsert `wetravel_trips`.
3. Upsert `trip_settings`.
4. Upsert `users`, `trip_travelers`, `traveler_profiles`, and `traveler_products` only if that table exists.
5. Write a local audit JSON/CSV under `backend/outputs/casamento-garapha`.

### Task 4: Implement Google Sheets Updates

**Files:**
- Modify: `backend/scripts/seed_casamento_garapha.py`

**Steps:**
1. Reuse the existing OAuth token and client file under `backend/secrets`.
2. Update only matching trip UUID rows in `Viagens` and `Viajantes Teste`.
3. Preserve unrelated rows.
4. Support `--skip-sheets` for database-only runs.

### Task 5: Execute and Verify

**Commands:**
- `cd backend && .venv/bin/python -m pytest tests/scripts/test_seed_casamento_garapha.py -q`
- `cd backend && .venv/bin/python scripts/seed_casamento_garapha.py`
- `cd backend && .venv/bin/python scripts/seed_casamento_garapha.py --execute`

**Verification:**
- Supabase contains one trip row for `CASAMENTO-GARAPHA-2026`.
- Supabase contains two traveler users and two `trip_travelers` links.
- Sheets contain the trip row and two traveler audit rows.


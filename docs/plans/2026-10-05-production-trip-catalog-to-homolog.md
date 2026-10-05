# Production Trip Catalog to Homologation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Synchronize the non-personal production trip catalog into homologation and make exactly three approved validators staff members of every copied trip.

**Architecture:** Add an allowlisted Python synchronization script that opens production as a read source and homologation as a transactional write target. Preserve catalog UUIDs, rebuild homologation in foreign-key-safe order, create only the three approved users, and verify invariants before commit. Dry-run is the default and execution requires an explicit flag.

**Tech Stack:** Python 3.12, asyncpg, pytest, PostgreSQL/Supabase, existing backend virtual environment.

---

### Task 1: Define the synchronization contract and safety guards

**Files:**
- Create: `backend/scripts/sync_production_catalog_to_homolog.py`
- Create: `backend/tests/scripts/test_sync_production_catalog_to_homolog.py`

**Step 1: Write failing tests**

Add tests asserting:

- the three validators are identified by the approved email addresses;
- the included table list contains only catalog/content tables;
- traveler, financial, webhook, OTP, announcement, and task tables are excluded;
- execution refuses missing URLs and identical production/homologation targets;
- dry-run is the default and `--execute` is required for writes.

**Step 2: Run the tests and verify RED**

Run:

```bash
cd backend && .venv/bin/pytest tests/scripts/test_sync_production_catalog_to_homolog.py -q
```

Expected: failure because the synchronization module does not exist.

**Step 3: Implement the minimal contract**

Define immutable constants for validator emails, catalog tables in insertion
order, deletion order, and excluded tables. Add argument parsing for:

```text
--production-database-url
--homologation-database-url
--execute
```

Validate both URLs, normalize driver prefixes, compare database identities, and
never print either URL.

**Step 4: Run the focused tests and verify GREEN**

Run the same pytest command and expect all tests to pass.

**Step 5: Commit**

```bash
git add backend/scripts/sync_production_catalog_to_homolog.py backend/tests/scripts/test_sync_production_catalog_to_homolog.py
git commit -m "feat: define safe homolog catalog sync"
```

### Task 2: Read and validate the production catalog

**Files:**
- Modify: `backend/scripts/sync_production_catalog_to_homolog.py`
- Modify: `backend/tests/scripts/test_sync_production_catalog_to_homolog.py`

**Step 1: Write failing tests**

Use temporary PostgreSQL test databases/fixtures to assert that the source
reader:

- loads all included rows and columns;
- orders parent phases before child phases;
- finds exactly one active staff user for every approved email;
- fails on a missing/duplicate validator;
- returns table counts and the set of trip UUIDs;
- never reads rows from excluded tables.

**Step 2: Run the focused tests and verify RED**

Expected: failures for the missing source reader.

**Step 3: Implement the source snapshot**

Read table metadata from PostgreSQL for allowlisted tables, fetch rows as typed
records, validate internal references, and build a snapshot object. Read only
the three approved users. Produce a redacted count summary.

**Step 4: Run the focused tests and verify GREEN**

Expected: all focused tests pass.

**Step 5: Commit**

```bash
git add backend/scripts/sync_production_catalog_to_homolog.py backend/tests/scripts/test_sync_production_catalog_to_homolog.py
git commit -m "feat: read validated production trip catalog"
```

### Task 3: Rebuild homologation transactionally

**Files:**
- Modify: `backend/scripts/sync_production_catalog_to_homolog.py`
- Modify: `backend/tests/scripts/test_sync_production_catalog_to_homolog.py`

**Step 1: Write failing tests**

Assert that execute mode:

- clears catalog dependents in foreign-key-safe order;
- clears all excluded user/operational tables in homologation;
- inserts the catalog with source IDs preserved;
- inserts exactly the three validator users;
- creates `trip count * 3` unique `trip_staff` rows;
- is idempotent across two consecutive runs;
- rolls back every target change after a forced failure.

**Step 2: Run the focused tests and verify RED**

Expected: failures for missing target synchronization behavior.

**Step 3: Implement one-transaction execution**

Inside one homologation transaction:

1. lock the relevant target tables;
2. delete excluded operational rows and existing catalog rows in safe order;
3. bulk insert the catalog in dependency order;
4. insert the three users with source identity fields and role `staff`;
5. generate deterministic staff membership UUIDs for every user/trip pair;
6. validate counts, roles, unique memberships, and excluded-table emptiness;
7. commit only after all invariants pass.

The production connection performs `SELECT` statements only.

**Step 4: Run the focused tests and verify GREEN**

Expected: all focused tests pass, including rollback and second-run tests.

**Step 5: Commit**

```bash
git add backend/scripts/sync_production_catalog_to_homolog.py backend/tests/scripts/test_sync_production_catalog_to_homolog.py
git commit -m "feat: rebuild homolog catalog transactionally"
```

### Task 4: Add an operator command and documentation

**Files:**
- Modify: `Makefile`
- Modify: `README.md`
- Modify: `backend/tests/scripts/test_sync_production_catalog_to_homolog.py`

**Step 1: Write a failing command/configuration test**

Assert that the Make target passes separate production and homologation URLs,
defaults to dry-run, and requires an explicit execute target for mutation.

**Step 2: Run the test and verify RED**

Expected: failure because the targets do not exist.

**Step 3: Add targets**

Add:

```text
sync-homolog-catalog-dry-run
sync-homolog-catalog-execute
```

The production URL comes from `backend/.env.production`; the homologation URL
must be supplied from the dedicated local secret/keychain path. Document scope,
safety guarantees, and expected summaries without documenting secrets.

**Step 4: Run tests and verify GREEN**

Run the focused script tests and Makefile configuration guard.

**Step 5: Commit**

```bash
git add Makefile README.md backend/tests/scripts/test_sync_production_catalog_to_homolog.py
git commit -m "docs: add homolog catalog sync runbook"
```

### Task 5: Validate and execute against Supabase

**Files:**
- No source changes expected.

**Step 1: Run the backend test suite**

```bash
cd backend && .venv/bin/pytest -q
```

Expected: all tests pass.

**Step 2: Capture fresh pre-execution counts**

Query production and homologation for included and excluded table counts. Do not
display phone numbers, database URLs, or secrets.

**Step 3: Run dry-run**

Execute `make sync-homolog-catalog-dry-run` and compare its summary with the
direct production counts. Expected: no homologation rows change.

**Step 4: Execute the synchronization**

Execute `make sync-homolog-catalog-execute`. Expected: transaction commits and
reports all invariants satisfied.

**Step 5: Verify the target independently**

Confirm:

- included table counts equal the production snapshot;
- `users = 3` and every role is `staff`;
- `trip_staff = trip count * 3`;
- each trip has all three distinct staff users;
- excluded tables are empty;
- OTP requests for all three approved phones return success/debug codes rather
  than authorization errors;
- production counts and rows are unchanged.

**Step 6: Commit any generated documentation only if needed**

No secrets or production data may be committed.

### Task 6: Final review and delivery

**Files:**
- Review all files changed by Tasks 1-4.

**Step 1: Inspect the complete diff**

```bash
git diff origin/homologacao...HEAD
git status --short
```

**Step 2: Run final focused and full verification**

Repeat the script test file, full backend suite, dry-run, and independent target
invariant queries.

**Step 3: Push the homologation branch**

```bash
git push origin homologacao
```

Expected: remote branch contains the design, implementation, tests, and runbook.


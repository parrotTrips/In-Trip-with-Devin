# Simplify Trip Travelers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `display_name`, `enrollment_status`, and `joined_at` from `trip_travelers` across the active database modeling docs and DBML artifact, while keeping `id` and `UNIQUE (trip_id, user_id)`.

**Architecture:** This is a documentation-first schema simplification. The implementation updates the canonical model docs and the DBML artifact so `trip_travelers` remains the association entity between users and trips, but no longer stores redundant participation fields with no current product use.

**Tech Stack:** Markdown documentation, DBML

---

### Task 1: Update the conceptual and logical model docs

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/02-erd-conceitual.md`
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
- Modify: `MODELO_BANCO_DE_DADOS/04-vertabelo.md`

**Step 1: Remove obsolete trip traveler fields**

Delete `display_name`, `enrollment_status`, and `joined_at` from the `trip_travelers` field lists in the three model docs.

**Step 2: Remove field-specific checks**

Delete the `enrollment_status` check from the Vertabelo-oriented model doc.

**Step 3: Verify the docs**

Run: `rg -n 'display_name|enrollment_status|joined_at' MODELO_BANCO_DE_DADOS/02-erd-conceitual.md MODELO_BANCO_DE_DADOS/03-modelo-logico.md MODELO_BANCO_DE_DADOS/04-vertabelo.md`
Expected: no matches remain in those active modeling docs.

### Task 2: Update the DBML artifact

**Files:**
- Modify: `docs/db/parrot-trips-erd.dbml`

**Step 1: Remove the obsolete fields from `trip_travelers`**

Delete `display_name`, `enrollment_status`, and `joined_at` from `Table trip_travelers`.

**Step 2: Preserve the association identity**

Keep `id`, `trip_id`, `user_id`, `created_at`, `updated_at`, and the `UNIQUE (trip_id, user_id)` index.

**Step 3: Verify the DBML**

Run: `sed -n '29,42p' docs/db/parrot-trips-erd.dbml`
Expected: the `trip_travelers` table contains only `id`, `trip_id`, `user_id`, `created_at`, `updated_at`, plus the unique composite index.

### Task 3: Run a repository verification pass

**Files:**
- Verify: `MODELO_BANCO_DE_DADOS/`
- Verify: `docs/db/`

**Step 1: Search for stale field references**

Run: `rg -n 'display_name|enrollment_status|joined_at' MODELO_BANCO_DE_DADOS docs/db`
Expected: no active model references remain.

**Step 2: Confirm the new design doc exists**

Run: `sed -n '1,200p' docs/plans/2026-04-06-simplify-trip-travelers-design.md`
Expected: the design file explains why `trip_travelers.id` is preserved while the three extra fields are removed.

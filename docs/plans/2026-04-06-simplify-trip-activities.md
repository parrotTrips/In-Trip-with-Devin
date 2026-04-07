# Simplify Trip Activities Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `activity_code`, `price_label`, and `vibe`, add `amount_brl`, and remove the old activity-code uniqueness rule from `trip_activities` across the active schema docs and DBML artifact.

**Architecture:** This is a documentation-first schema simplification with one small active mock-data cleanup in the frontend. The implementation updates the DBML artifact, the canonical modeling docs, and the active frontend mock type/data so all current references reflect the same leaner activity model.

**Tech Stack:** Markdown documentation, DBML, TypeScript

---

### Task 1: Update the active model docs

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
- Modify: `MODELO_BANCO_DE_DADOS/04-vertabelo.md`

**Step 1: Replace the old activity fields**

Remove `activity_code`, `price_label`, and `vibe`, then add `amount_brl` in the `trip_activities` field lists.

**Step 2: Remove the old uniqueness rule**

Delete `UNIQUE (trip_phase_id, activity_code)` from the Vertabelo doc.

**Step 3: Verify the docs**

Run: `rg -n 'activity_code|price_label|vibe|UNIQUE \\(trip_phase_id, activity_code\\)|amount_brl' MODELO_BANCO_DE_DADOS/03-modelo-logico.md MODELO_BANCO_DE_DADOS/04-vertabelo.md`
Expected: only `amount_brl` remains in the active model docs.

### Task 2: Update the DBML artifact

**Files:**
- Modify: `docs/db/parrot-trips-erd.dbml`

**Step 1: Replace the old fields**

Remove `activity_code`, `price_label`, and `vibe`, add `amount_brl numeric(12,2)`, and remove the `(trip_phase_id, activity_code)` unique index.

**Step 2: Verify the artifact**

Run: `sed -n '150,166p' docs/db/parrot-trips-erd.dbml`
Expected: the activity table contains `amount_brl` and no removed fields or old unique index.

### Task 3: Align related active references

**Files:**
- Modify: `docs/plans/2026-04-06-remove-trip-slugs-design.md`
- Modify: `frontend/src/data/tripData.ts`

**Step 1: Remove the stale design statement**

Delete the statement that says the model keeps `activity_code` as a stable identifier.

**Step 2: Remove unused `vibe` from the active mock data shape**

Delete the `vibe` property from the `Activity` interface and remove the `vibe:` entries from the mock activity objects in `frontend/src/data/tripData.ts`.

**Step 3: Verify the related references**

Run: `rg -n 'activity_code|vibe' docs/plans/2026-04-06-remove-trip-slugs-design.md frontend/src/data/tripData.ts`
Expected: no stale `activity_code` reference remains in the design doc, and `vibe` is removed from the active frontend mock file.

### Task 4: Run a repository verification pass

**Files:**
- Verify: `MODELO_BANCO_DE_DADOS/`
- Verify: `docs/db/`
- Verify: `frontend/src/data/tripData.ts`

**Step 1: Search active references**

Run: `rg -n 'activity_code|price_label|vibe|trip_phase_id, activity_code' MODELO_BANCO_DE_DADOS docs/db frontend/src/data/tripData.ts`
Expected: no active references remain.

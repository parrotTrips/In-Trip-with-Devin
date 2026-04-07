# Remove Checklist Item Code Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `item_code` and `UNIQUE (trip_phase_id, item_code)` from `trip_phase_checklist_items` across the active database modeling docs and DBML artifact.

**Architecture:** This is a narrow documentation-first schema simplification. The implementation updates the DBML artifact, the canonical model docs, and one prior design doc so all active references consistently describe checklist items without a separate textual code.

**Tech Stack:** Markdown documentation, DBML

---

### Task 1: Update the active model docs

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
- Modify: `MODELO_BANCO_DE_DADOS/04-vertabelo.md`

**Step 1: Remove `item_code` from the field lists**

Delete `item_code` from the `trip_phase_checklist_items` field lists.

**Step 2: Remove the old uniqueness rule**

Delete `UNIQUE (trip_phase_id, item_code)` from the Vertabelo-oriented model doc.

**Step 3: Verify the docs**

Run: `rg -n 'item_code|UNIQUE \\(trip_phase_id, item_code\\)' MODELO_BANCO_DE_DADOS/03-modelo-logico.md MODELO_BANCO_DE_DADOS/04-vertabelo.md`
Expected: no matches remain.

### Task 2: Update the DBML artifact

**Files:**
- Modify: `docs/db/parrot-trips-erd.dbml`

**Step 1: Remove the field and index**

Delete `item_code` from `trip_phase_checklist_items` and remove the `(trip_phase_id, item_code)` unique index.

**Step 2: Verify the artifact**

Run: `sed -n '118,130p' docs/db/parrot-trips-erd.dbml`
Expected: the checklist table contains no `item_code` field and no unique index block.

### Task 3: Align prior planning docs

**Files:**
- Modify: `docs/plans/2026-04-06-remove-trip-slugs-design.md`

**Step 1: Remove the stale statement**

Delete the statement that says the model keeps `item_code` as a stable identifier.

**Step 2: Verify the plan doc**

Run: `rg -n 'item_code' docs/plans/2026-04-06-remove-trip-slugs-design.md`
Expected: no stale reference remains there.

### Task 4: Run a repository verification pass

**Files:**
- Verify: `MODELO_BANCO_DE_DADOS/`
- Verify: `docs/db/`
- Verify: `docs/plans/`

**Step 1: Search active references**

Run: `rg -n 'item_code|trip_phase_id, item_code' MODELO_BANCO_DE_DADOS docs/db docs/plans`
Expected: only references inside this new removal plan/design may remain.

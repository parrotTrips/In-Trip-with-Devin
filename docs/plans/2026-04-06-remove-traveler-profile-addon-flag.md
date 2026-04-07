# Remove Traveler Profile Addon Flag Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `receive_addon_updates_flag` from `traveler_profiles` across the active database modeling docs and DBML artifact.

**Architecture:** This is a narrow documentation-first schema simplification. The implementation updates the DBML artifact and the logical model doc so both active sources describe the same leaner traveler profile structure without the add-on updates consent field.

**Tech Stack:** Markdown documentation, DBML

---

### Task 1: Update the active model docs

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`

**Step 1: Remove the field from the logical model**

Delete `receive_addon_updates_flag` from the `traveler_profiles` field list.

**Step 2: Verify the doc**

Run: `rg -n 'receive_addon_updates_flag' MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
Expected: no matches remain.

### Task 2: Update the DBML artifact

**Files:**
- Modify: `docs/db/parrot-trips-erd.dbml`

**Step 1: Remove the field from `traveler_profiles`**

Delete `receive_addon_updates_flag` from the `traveler_profiles` table.

**Step 2: Verify the DBML**

Run: `rg -n 'receive_addon_updates_flag' docs/db/parrot-trips-erd.dbml`
Expected: no matches remain.

### Task 3: Run a repository verification pass

**Files:**
- Verify: `MODELO_BANCO_DE_DADOS/`
- Verify: `docs/db/`

**Step 1: Search active model sources**

Run: `rg -n 'receive_addon_updates_flag' MODELO_BANCO_DE_DADOS docs/db`
Expected: no active model references remain.

**Step 2: Confirm the design doc exists**

Run: `sed -n '1,200p' docs/plans/2026-04-06-remove-traveler-profile-addon-flag-design.md`
Expected: the design doc describes the approved removal.

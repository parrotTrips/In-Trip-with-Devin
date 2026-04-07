# Remove Phase Attachments Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `trip_phase_attachments` and the active phase attachments UI/mock concept from the current schema docs, DBML artifact, DB diagram artifact, and frontend phase screen.

**Architecture:** This is a documentation-first schema simplification with a small active frontend cleanup. The implementation removes the entity from the canonical model docs and visual artifacts, then removes the mock `attachments` shape and the "Documents" rendering block from the active phase details screen so the UI matches the simplified product scope.

**Tech Stack:** Markdown documentation, DBML, dbdiagram JSON, TypeScript/React

---

### Task 1: Update the active model docs

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/02-erd-conceitual.md`
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
- Modify: `MODELO_BANCO_DE_DADOS/04-vertabelo.md`
- Modify: `MODELO_BANCO_DE_DADOS/05-cardinalidades.md`
- Modify: `MODELO_BANCO_DE_DADOS/06-midia-e-storage.md`

**Step 1: Remove the entity**

Delete the `trip_phase_attachments` section from the active model docs.

**Step 2: Remove related relationships**

Delete the catalog/cardinality relationships that mention `TripPhaseAttachment`.

**Step 3: Remove storage-specific mention**

Delete the `trip_phase_attachments` subsection from the media/storage doc.

**Step 4: Verify the docs**

Run: `rg -n 'trip_phase_attachments|TripPhaseAttachment' MODELO_BANCO_DE_DADOS`
Expected: no active references remain.

### Task 2: Update the DBML and DB diagram artifacts

**Files:**
- Modify: `docs/db/parrot-trips-erd.dbml`
- Modify: `docs/db/parrot-trips-erd.dbdiagram`

**Step 1: Remove the DBML table**

Delete `Table trip_phase_attachments` from the DBML artifact.

**Step 2: Remove the visual artifact references**

Delete the `trip_phase_attachments` table position and its two reference paths from the dbdiagram JSON.

**Step 3: Verify the artifacts**

Run: `rg -n 'trip_phase_attachments' docs/db`
Expected: no references remain in the active DB artifacts.

### Task 3: Remove the active frontend attachments concept

**Files:**
- Modify: `frontend/src/data/tripData.ts`
- Modify: `frontend/src/features/trip/pages/PhaseDetails.tsx`

**Step 1: Remove the mock shape**

Delete `attachments` from the `Phase` interface and remove any `attachments:` data from the mock phases.

**Step 2: Remove the UI block**

Delete the "Documents" section from `PhaseDetails.tsx` and remove any now-unused import tied to that block.

**Step 3: Verify the frontend**

Run: `rg -n 'attachments\\?|attachments:|phase\\.attachments|Documents' frontend/src/data/tripData.ts frontend/src/features/trip/pages/PhaseDetails.tsx`
Expected: no stale active frontend references remain.

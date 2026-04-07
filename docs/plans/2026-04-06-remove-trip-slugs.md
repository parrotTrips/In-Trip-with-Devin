# Remove Trip Slugs and Timezone Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `trips.slug`, `trips.default_timezone`, `trip_phases.slug`, and the `(trip_id, slug)` uniqueness rule from the current database modeling docs and DBML artifact.

**Architecture:** This is a documentation-first schema simplification. The implementation updates the canonical database modeling docs, the DBML ERD artifact, and the ERD planning docs so they all describe the same leaner trip model without slug-based identifiers or trip-level timezone configuration.

**Tech Stack:** Markdown documentation, DBML

---

### Task 1: Update the conceptual and logical models

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/02-erd-conceitual.md`
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
- Modify: `MODELO_BANCO_DE_DADOS/04-vertabelo.md`

**Step 1: Remove obsolete trip fields**

Delete `slug` and `default_timezone` from the `trips` field lists in the three modeling docs.

**Step 2: Remove the phase slug**

Delete `slug` from the `trip_phases` field lists in the same modeling docs.

**Step 3: Remove the old uniqueness rule**

Delete the `UNIQUE (trip_id, slug)` rule from the Vertabelo-oriented model doc.

**Step 4: Verify the model docs**

Run: `rg -n '^- `slug`$|default_timezone|UNIQUE \\(trip_id, slug\\)' MODELO_BANCO_DE_DADOS/02-erd-conceitual.md MODELO_BANCO_DE_DADOS/03-modelo-logico.md MODELO_BANCO_DE_DADOS/04-vertabelo.md`
Expected: no matches remain for those removed trip fields and rule.

### Task 2: Update the DBML artifact

**Files:**
- Modify: `docs/db/parrot-trips-erd.dbml`

**Step 1: Remove the trip fields**

Delete `slug` and `default_timezone` from `Table trips`.

**Step 2: Remove the phase slug and unique index**

Delete `slug` from `Table trip_phases` and remove the `(trip_id, slug)` unique index block.

**Step 3: Verify the artifact**

Run: `rg -n 'default_timezone|\\bslug\\b|\\(trip_id, slug\\)' docs/db/parrot-trips-erd.dbml`
Expected: only non-trip uses of `slug` remain if any; no trip or trip-phase slug fields and no `(trip_id, slug)` index remain.

### Task 3: Align the ERD planning docs

**Files:**
- Modify: `docs/plans/2026-04-06-dbml-erd-design.md`
- Modify: `docs/plans/2026-04-06-dbml-erd.md`

**Step 1: Remove the outdated uniqueness reference**

Delete the `trip_phases (trip_id, slug)` example from the ERD design doc.

**Step 2: Update the verification command**

Adjust the ERD implementation plan so its verification step no longer checks for `(trip_id, slug)`.

**Step 3: Verify the planning docs**

Run: `rg -n '\\(trip_id, slug\\)|default_timezone|^- `slug`$' docs/plans/2026-04-06-dbml-erd-design.md docs/plans/2026-04-06-dbml-erd.md`
Expected: no stale references remain in those planning docs.

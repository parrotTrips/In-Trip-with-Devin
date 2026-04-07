# Traveler-Only Domain Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `users.role` and all structural backoffice/internal-user assumptions from the current database modeling docs and DBML artifact.

**Architecture:** This is a documentation-first domain simplification. The implementation updates the canonical modeling documents and the derived DBML ERD so they all describe a traveler-only product scope, while preserving the existing traveler-in-trip relational structure.

**Tech Stack:** Markdown documentation, DBML

---

### Task 1: Record the traveler-only domain in the design and scope docs

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/README.md`
- Modify: `MODELO_BANCO_DE_DADOS/01-contexto-e-decisoes.md`

**Step 1: Update the repository-level database scope**

Remove the backoffice statement from the current scope in `MODELO_BANCO_DE_DADOS/README.md`.

**Step 2: Update context and decisions**

Rewrite the context and closed decisions in `MODELO_BANCO_DE_DADOS/01-contexto-e-decisoes.md` so they describe a traveler-only product and no longer reference internal users or backoffice operations.

**Step 3: Verify the wording**

Run: `rg -n 'backoffice|usu[aá]rios internos|team|admin' MODELO_BANCO_DE_DADOS/README.md MODELO_BANCO_DE_DADOS/01-contexto-e-decisoes.md`
Expected: no structural references remain in those files.

### Task 2: Remove `users.role` from the conceptual and logical models

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/02-erd-conceitual.md`
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
- Modify: `MODELO_BANCO_DE_DADOS/04-vertabelo.md`

**Step 1: Update the `users` entity descriptions**

Remove the `role` field from the `users` attribute lists and rewrite the surrounding narrative so `users` represents travelers only.

**Step 2: Remove role-specific checks**

Delete the `role` column and its allowed-values check from the Vertabelo-oriented model doc.

**Step 3: Verify the model docs**

Run: `rg -n '^- `role`|role text|role in' MODELO_BANCO_DE_DADOS/02-erd-conceitual.md MODELO_BANCO_DE_DADOS/03-modelo-logico.md MODELO_BANCO_DE_DADOS/04-vertabelo.md`
Expected: no remaining model references to `users.role`.

### Task 3: Update the DBML artifact

**Files:**
- Modify: `docs/db/parrot-trips-erd.dbml`

**Step 1: Remove the `role` column from `users`**

Delete the `role` field from the `users` table in the DBML file.

**Step 2: Verify the artifact**

Run: `sed -n '8,17p' docs/db/parrot-trips-erd.dbml`
Expected: the `users` table lists `id`, `phone`, `full_name`, `email`, `status`, `created_at`, and `updated_at`, without `role`.

### Task 4: Run a repository verification pass for structural references

**Files:**
- Verify: `MODELO_BANCO_DE_DADOS/`
- Verify: `docs/db/`

**Step 1: Search for removed structural terms**

Run: `rg -n 'backoffice|usu[aá]rios internos|role text|role in|^- `role`$' MODELO_BANCO_DE_DADOS docs/db`
Expected: no remaining structural matches.

**Step 2: Confirm the new design docs exist**

Run: `sed -n '1,200p' docs/plans/2026-04-06-traveler-only-domain-design.md`
Expected: the design file describes the approved traveler-only domain.

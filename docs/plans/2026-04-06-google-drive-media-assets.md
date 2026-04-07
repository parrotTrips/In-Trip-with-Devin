# Google Drive Media Assets Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign `media_assets` to use a simple Google Drive-oriented schema and remove the generic storage fields plus `file_size_bytes`.

**Architecture:** This is a documentation-first schema redesign. The implementation updates the active DBML artifact and the canonical database-modeling docs so all sources describe `media_assets` as a lightweight reference to files organized in Google Drive folders and subfolders.

**Tech Stack:** Markdown documentation, DBML

---

### Task 1: Update the active model docs

**Files:**
- Modify: `MODELO_BANCO_DE_DADOS/03-modelo-logico.md`
- Modify: `MODELO_BANCO_DE_DADOS/04-vertabelo.md`
- Modify: `MODELO_BANCO_DE_DADOS/06-midia-e-storage.md`

**Step 1: Replace the generic field list**

Change the `media_assets` field list to:
- `id`
- `drive_file_id`
- `drive_path`
- `public_url`
- `mime_type`
- `original_filename`
- `created_at`
- `updated_at`

**Step 2: Replace the uniqueness rule**

Change the uniqueness rule in the Vertabelo doc from `UNIQUE (storage_provider, storage_key)` to `UNIQUE (drive_file_id)`.

**Step 3: Rewrite the storage rationale**

Update the media/storage doc so it explicitly describes Google Drive folders/subfolders as the chosen storage organization instead of generic external storage wording.

**Step 4: Verify the docs**

Run: `rg -n 'storage_provider|storage_bucket|storage_key|file_size_bytes|UNIQUE \\(storage_provider, storage_key\\)' MODELO_BANCO_DE_DADOS/03-modelo-logico.md MODELO_BANCO_DE_DADOS/04-vertabelo.md MODELO_BANCO_DE_DADOS/06-midia-e-storage.md`
Expected: no stale generic-storage references remain in those active docs.

### Task 2: Update the DBML artifact

**Files:**
- Modify: `docs/db/parrot-trips-erd.dbml`

**Step 1: Replace the media asset fields**

Update `Table media_assets` to use:
- `id`
- `drive_file_id`
- `drive_path`
- `public_url`
- `mime_type`
- `original_filename`
- `created_at`
- `updated_at`

**Step 2: Replace the unique index**

Change the DBML index from `(storage_provider, storage_key)` to `(drive_file_id)`.

**Step 3: Verify the artifact**

Run: `sed -n '84,100p' docs/db/parrot-trips-erd.dbml`
Expected: `media_assets` reflects the Google Drive-oriented schema with no generic storage fields.

### Task 3: Run a repository verification pass

**Files:**
- Verify: `MODELO_BANCO_DE_DADOS/`
- Verify: `docs/db/`

**Step 1: Search active model sources**

Run: `rg -n 'storage_provider|storage_bucket|storage_key|file_size_bytes' MODELO_BANCO_DE_DADOS docs/db`
Expected: no active generic-storage field references remain.

**Step 2: Confirm the design doc exists**

Run: `sed -n '1,200p' docs/plans/2026-04-06-google-drive-media-assets-design.md`
Expected: the design doc describes the approved Google Drive-oriented model.

# Root Docs Reorganization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move loose documentation and duplicate assets out of the repository root while preserving working app references.

**Architecture:** Keep root limited to project entry files. Put observability docs, data requests, testing notes, and prompts under focused `docs/` subdirectories. Preserve `frontend/public/parrot_icon.svg` as the favicon source.

**Tech Stack:** Markdown docs, Vite public assets, Git.

---

### Task 1: Move Loose Root Docs

**Files:**
- Move: `observabilidade.md` to `docs/observability/observabilidade.md`
- Restore and move: `guia-observabilidade.md` to `docs/observability/guia-observabilidade.md`
- Move: `20260806 - Data Request Casamento GaRapha.md` to `docs/data-requests/20260806-data-request-casamento-garapha.md`
- Move: `viagem_teste.md` to `docs/testing/viagem_teste.md`
- Move: `handoff_testes_parrot_ai.txt` to `docs/testing/handoff_testes_parrot_ai.txt`
- Move: `prompt_criar_viagem_wetravel_api.txt` to `docs/prompts/prompt_criar_viagem_wetravel_api.txt`

**Step 1: Create destination directories**

Run: `mkdir -p docs/observability docs/data-requests docs/testing docs/prompts`

**Step 2: Move tracked and untracked files**

Use `git mv` for tracked files and `mv` for untracked files.

**Step 3: Update references**

Search for old paths and replace them with the new `docs/` paths.

**Step 4: Verify root cleanliness**

Run: `find . -maxdepth 1 -type f -print | sort`

Expected: root keeps `.gitignore`, `Makefile`, `README.md`, and `resume.txt` only.

**Step 5: Verify no stale references**

Run: `rg "20260806 - Data Request Casamento GaRapha.md|observabilidade.md|guia-observabilidade.md|handoff_testes_parrot_ai|prompt_criar_viagem_wetravel_api|viagem_teste.md"`

Expected: only updated references remain.

### Task 2: Remove Duplicate Root Favicon

**Files:**
- Delete: `parrot_icon.svg` if identical to `frontend/public/parrot_icon.svg`

**Step 1: Compare files**

Run: `cmp -s parrot_icon.svg frontend/public/parrot_icon.svg`

Expected: exit code `0`.

**Step 2: Delete duplicate root file**

Delete `parrot_icon.svg` from the root. The app already references `/parrot_icon.svg`, which Vite serves from `frontend/public/parrot_icon.svg`.

**Step 3: Verify frontend favicon reference**

Run: `sed -n '1,12p' frontend/index.html`

Expected: `<link rel="icon" type="image/svg+xml" href="/parrot_icon.svg" />` remains unchanged.

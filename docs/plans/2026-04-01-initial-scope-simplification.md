# Initial Scope Simplification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce the active app to `Map` and `My Profile`, remove the side menu and inactive features, and document all removals for future reimplementation.

**Architecture:** Simplify navigation first, then shrink `My Profile`, then remove inactive frontend and backend modules. Preserve recoverability through a dedicated archive document instead of keeping dormant code in the active tree.

**Tech Stack:** React, TypeScript, React Router, Vitest, FastAPI, Python

---

### Task 1: Archive Documentation

**Files:**
- Create: `docs/archives/2026-04-01-initial-scope-simplification.md`
- Modify: `docs/plans/2026-04-01-initial-scope-simplification-design.md`

**Step 1: Write the archive document skeleton**

Document the removed frontend sections, removed backend sections, original file paths, and future rebuild notes.

**Step 2: Review the file list against the codebase**

Run: `find frontend/src/features -maxdepth 3 -type f | sort`
Expected: visible list of active and removable feature files

**Step 3: Finalize the archive notes**

Add exact routes, component names, and backend modules being removed.

**Step 4: Verify the document exists**

Run: `sed -n '1,240p' docs/archives/2026-04-01-initial-scope-simplification.md`
Expected: archive document content renders correctly

### Task 2: Navigation TDD

**Files:**
- Modify: `frontend/src/app/App.test.tsx`
- Modify: `frontend/src/shared/components/TopBar.test.tsx`

**Step 1: Write failing assertions for simplified navigation**

Assert that authenticated app composition shows `Map` and `My Profile`, and does not show `Secret Missions`, `Sharing XP`, `Local Recommendations`, or `Documents`.

**Step 2: Run the focused frontend tests to verify failure**

Run: `npm test -- --run frontend/src/app/App.test.tsx frontend/src/shared/components/TopBar.test.tsx`
Expected: FAIL because current UI still exposes removed navigation items

**Step 3: Implement minimal navigation changes**

Update `BottomNav`, `TopBar`, and `AppRouter` to match the reduced flow.

**Step 4: Re-run the focused tests**

Run: `npm test -- --run frontend/src/app/App.test.tsx frontend/src/shared/components/TopBar.test.tsx`
Expected: PASS

### Task 3: Profile Scope TDD

**Files:**
- Modify: `frontend/src/features/profile/ProfileScreen.test.tsx`
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`

**Step 1: Write failing assertions for the reduced profile scope**

Assert that `Registration Details`, `Products & Payment`, and `Service Agreement` remain, while `eSIM`, `Roommate`, and `Flight Information` are absent.

**Step 2: Run the focused profile test to verify failure**

Run: `npm test -- --run frontend/src/features/profile/ProfileScreen.test.tsx`
Expected: FAIL because the removed sections still render

**Step 3: Implement the minimal profile simplification**

Remove the unused sections and any now-unused traveler-loading logic or imports.

**Step 4: Re-run the focused profile test**

Run: `npm test -- --run frontend/src/features/profile/ProfileScreen.test.tsx`
Expected: PASS

### Task 4: Remove Inactive Frontend Modules

**Files:**
- Modify: `frontend/src/app/router.tsx`
- Delete: `frontend/src/features/missions/pages/MissionsScreen.tsx`
- Delete: `frontend/src/features/missions/services/missions-api.ts`
- Delete: `frontend/src/features/missions/MissionsScreen.test.tsx`
- Delete: `frontend/src/features/sharing/pages/SharingXPScreen.tsx`
- Delete: `frontend/src/features/recommendations/pages/RecommendationsScreen.tsx`
- Delete: `frontend/src/features/emergency/pages/EmergencyContacts.tsx`
- Delete: `frontend/src/features/documents/pages/DocumentsScreen.tsx`

**Step 1: Remove active route references**

Delete inactive imports and route entries from `router.tsx`.

**Step 2: Delete the inactive modules**

Remove the disconnected feature files once tests already describe the new active scope.

**Step 3: Run an architecture sanity check**

Run: `npm test -- --run frontend/src/app/pages-architecture.test.ts`
Expected: PASS

### Task 5: Remove Inactive Backend Missions Modules

**Files:**
- Modify: `backend/app/main.py`
- Delete: `backend/app/routers/missions.py`
- Delete: `backend/app/schemas/missions.py`
- Delete: `backend/app/services/mission_service.py`

**Step 1: Remove the missions router import and registration**

Update `main.py` so missions are no longer exposed.

**Step 2: Delete the inactive missions backend modules**

Remove router, schema, and service files after documenting their former role.

**Step 3: Run backend-adjacent tests only if they do not require unrelated local setup**

Run: `pytest backend/tests -q`
Expected: either PASS or a clearly reported pre-existing environment issue

### Task 6: Final Verification

**Files:**
- Modify: `docs/archives/2026-04-01-initial-scope-simplification.md`

**Step 1: Run the focused frontend test suite**

Run: `npm test -- --run frontend/src/app/App.test.tsx frontend/src/shared/components/TopBar.test.tsx frontend/src/features/profile/ProfileScreen.test.tsx frontend/src/app/pages-architecture.test.ts`
Expected: PASS

**Step 2: Review the worktree**

Run: `git status --short`
Expected: only intended simplification changes plus any pre-existing unrelated backend changes

**Step 3: Update the archive document with final removed file list**

Add the exact files removed and the final active navigation state.

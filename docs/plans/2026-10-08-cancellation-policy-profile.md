# Cancellation Policy in My Profile Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Publish the existing My Profile cancellation-policy and package layout in both `main` and `homologacao`.

**Architecture:** Reuse the isolated historical implementation from commit `d006742`. Integrate it into `main`, verify the focused frontend behavior and build, then merge `main` into `homologacao` so homologation-only Staff changes remain intact.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Git.

---

### Task 1: Prove the regression tests detect the missing behavior

**Files:**
- Test: `frontend/src/features/profile/ProfileScreen.test.tsx`
- Test: `frontend/src/features/team/InformationScreen.test.tsx`

1. Apply only the test changes from `d006742` to the current `main` worktree.
2. Run the two focused test files and confirm they fail because the policy is still in Information and absent from My Profile.
3. Restore the temporary test-only changes.

### Task 2: Integrate the historical implementation into main

**Files:**
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`
- Modify: `frontend/src/features/team/pages/InformationScreen.tsx`
- Test: `frontend/src/features/profile/ProfileScreen.test.tsx`
- Test: `frontend/src/features/team/InformationScreen.test.tsx`

1. Cherry-pick commit `d006742`.
2. Run the focused tests and confirm they pass.
3. Run the frontend production build.
4. Push `main` only after both commands pass.

### Task 3: Propagate main into homologation

**Files:**
- Merge-only integration; preserve homologation-specific Staff and notification commits.

1. Merge updated `main` into `homologacao`.
2. Run the focused tests and frontend build on the merge result.
3. Push `homologacao` only after verification succeeds.

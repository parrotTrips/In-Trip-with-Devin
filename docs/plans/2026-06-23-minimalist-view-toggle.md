# Minimalist View Toggle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the top traveler-preview banner with a minimal floating control that lets a staff user return from traveler view in both development and production.

**Architecture:** Keep the existing `viewingAsTraveler` state in `AppContent`, but move the exit affordance into a small floating button rendered alongside the app shell. The button should only appear while a staff user is previewing traveler mode. The existing dev user switcher stays separate so identity switching does not get mixed with preview exit behavior.

**Tech Stack:** React, TypeScript, Tailwind CSS, Vitest, React Testing Library

---

### Task 1: Remove the top banner and add a floating return button

**Files:**
- Modify: `frontend/src/app/App.tsx`

**Step 1: Inspect the current preview state wiring**

Confirm `viewingAsTraveler` still lives in `AppContent` and that the exit action only needs to flip that state back to `false`.

**Step 2: Implement the minimal button**

Render a small fixed button near the bottom-right corner when `user?.role === 'staff' && viewingAsTraveler`.
Keep the label short and make the control unobtrusive.

**Step 3: Remove the top banner**

Delete the `TravelerViewBanner` component and remove the top padding workaround that existed only to make room for it.

**Step 4: Run the relevant frontend tests**

Run: `cd frontend && npm test -- --runInBand src/app/App.test.tsx`

Expected: PASS

---

### Task 2: Verify layout and build behavior

**Files:**
- Modify: `frontend/src/app/App.test.tsx` if coverage needs to reflect the new UI behavior

**Step 1: Check whether the existing tests still describe the app correctly**

The route assertions should continue to work. Add a focused assertion only if the removed banner had test coverage.

**Step 2: Run the full frontend test suite**

Run: `cd frontend && npm test -- --runInBand`

Expected: PASS

**Step 3: Run the frontend production build**

Run: `cd frontend && npm run build`

Expected: build completes without TypeScript or bundling errors


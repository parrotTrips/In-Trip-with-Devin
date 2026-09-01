# Journey Sticky Current Phase Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Journey summary stay visible during scroll and auto-center the current phase when the Journey opens.

**Architecture:** Update `HomeScreen.tsx` only for runtime behavior. The existing trip context already provides `phases`, `travelers`, and `current_phase_id`; use those values to attach a ref to the current phase card and run a guarded scroll effect after loading finishes.

**Tech Stack:** React, TypeScript, Tailwind CSS, Vitest, React Testing Library.

---

### Task 1: Sticky Journey Header

**Files:**
- Modify: `frontend/src/features/trip/pages/HomeScreen.tsx`
- Test: `frontend/src/features/trip/HomeScreen.test.tsx`

**Step 1: Write the failing test**

Add a test that renders the home screen and expects a `data-testid="journey-sticky-header"` element to have sticky positioning classes.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- HomeScreen.test.tsx --runInBand`

Expected: FAIL because `journey-sticky-header` does not exist.

**Step 3: Write minimal implementation**

Move the Journey hero wrapper from normal flow into a sticky block below the fixed app header:

- add `data-testid="journey-sticky-header"`;
- use `sticky top-14 z-50`;
- keep the existing visual content unchanged.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- HomeScreen.test.tsx --runInBand`

Expected: PASS.

### Task 2: Auto-Center Current Phase

**Files:**
- Modify: `frontend/src/features/trip/pages/HomeScreen.tsx`
- Test: `frontend/src/features/trip/HomeScreen.test.tsx`

**Step 1: Write the failing test**

Add multiple phases to the test fixture. Spy on `HTMLElement.prototype.scrollIntoView`, render the home screen with `currentPhaseId` set to a later phase, and expect `scrollIntoView` to be called with `{ block: 'center' }`.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- HomeScreen.test.tsx --runInBand`

Expected: FAIL because no auto-scroll effect exists.

**Step 3: Write minimal implementation**

In `HomeScreen.tsx`:

- import `useEffect` and `useRef`;
- create a ref for the current phase wrapper;
- after `loading` is false and `currentUserPhaseId` exists, call `scrollIntoView({ block: 'center', inline: 'nearest' })`;
- skip the effect if the phase ref is missing.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- HomeScreen.test.tsx --runInBand`

Expected: PASS.

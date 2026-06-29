# Traveler Card Badges Hover Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Keep traveler Pre Trip and In Trip card badges aligned and visible during hover.

**Architecture:** The traveler home renders both Pre Trip and In Trip cards from `HomeScreen.tsx`. Replace separate absolutely positioned mascot/check elements with one absolute badge container inside the card. Keep card hover as a transform on the card while the badges move as a single group.

**Tech Stack:** React, TypeScript, Tailwind CSS, Vitest, React Testing Library.

---

### Task 1: Add Regression Test

**Files:**
- Modify: `frontend/src/features/trip/HomeScreen.test.tsx`

**Step 1: Write failing test**

Add a test where the same phase is both ideal pace and already completed. Assert that one badge group renders and contains both the parrot mascot and completed check.

**Step 2: Run test to verify failure**

Run:

```bash
cd frontend
npm test -- --run src/features/trip/HomeScreen.test.tsx
```

Expected: fail because `data-testid="phase-card-badges"` does not exist yet.

### Task 2: Implement Badge Container

**Files:**
- Modify: `frontend/src/features/trip/pages/HomeScreen.tsx`

**Step 1: Update card classes**

Add `overflow-visible`, `transform-gpu`, and a smaller scale value.

**Step 2: Replace separate badge positions**

Create one absolute badge container with flex layout and fixed gap.

**Step 3: Add test ids**

Add `data-testid="phase-card-badges"`, `data-testid="phase-parrot-badge"`, and `data-testid="phase-completed-badge"`.

### Task 3: Verify

**Step 1: Run focused test**

```bash
cd frontend
npm test -- --run src/features/trip/HomeScreen.test.tsx
```

**Step 2: Run build**

```bash
cd frontend
npm run build
```


# Progress Bar Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the progress bar so it starts at 0% for new users, regresses when a phase is unmarked, and never jumps to 0% when all pre-trip phases are completed.

**Architecture:** All changes are pure frontend — two files only. The root cause is that `ProgressBar` uses `currentPhaseOrder + 1` as the numerator, treating the index of the current phase as completed count instead of the count of phases actually completed before it. Renaming the props to `completedCount`/`parrotCompletedCount` and removing the `+1` from the formula fixes both bugs cleanly. The backend `current_phase_id` (= first incomplete phase) is already the correct signal — we just need to count phases before it, not index it.

**Tech Stack:** React 18, TypeScript, Tailwind CSS

---

## Context — current behaviour and bugs

### Bug 1: bar starts non-zero for new users

`currentUserIdx = progressPhases.findIndex(p => p.id === currentUserPhaseId)`

For a user with no completed phases, the backend returns the first phase as `current_phase_id` (index 0). `ProgressBar` calculates `(0+1)/total * 100 = 1/total * 100` — never 0%.

### Bug 2: bar jumps to 0% after all pre-trip phases completed

When all pre-trip phases are marked done, the backend returns the first in-trip day as `current_phase_id`. Since `progressPhases` filters to `pre-trip` only (trip hasn't started), `findIndex` returns -1. `ProgressBar` calculates `(-1+1)/total * 100 = 0%`.

### Fix

Replace the `+1` semantics with a **completed count** semantic:

- `completedCount = progressPhases.findIndex(p => p.id === currentUserPhaseId)`
  - = 0 when on first phase (0 phases completed) ✅
  - = N when N phases are done ✅
  - = -1 when `currentUserPhaseId` is not in `progressPhases` → treat as `total` (all done) ✅
- Formula: `completedCount / totalPhases * 100` (no `+1`)

Same logic for parrot: count how many in-trip phases have `starts_at <= today`, not "index of current day + 1".

---

## File Map

| File | Action | What changes |
|---|---|---|
| `frontend/src/shared/components/ProgressBar.tsx` | Modify | Rename props `currentPhaseOrder`→`completedCount`, `parrotPhaseOrder`→`parrotCompletedCount`; remove `+1` from formula |
| `frontend/src/features/trip/pages/HomeScreen.tsx` | Modify | Rename variables to match; handle -1 (all complete) as `totalPhases`; fix parrot count logic |

---

## Task 1: Fix ProgressBar component props and formula

**Files:**
- Modify: `frontend/src/shared/components/ProgressBar.tsx`

- [ ] **Step 1: Replace the entire file content**

File path: `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend/src/shared/components/ProgressBar.tsx`

```tsx
interface Props {
  totalPhases: number;
  completedCount: number;
  parrotCompletedCount: number;
}

export default function ProgressBar({ totalPhases, completedCount, parrotCompletedCount }: Props) {
  if (totalPhases === 0) return null;

  const userProgress = Math.round((completedCount / totalPhases) * 100);
  const parrotProgress = Math.round((parrotCompletedCount / totalPhases) * 100);
  const isBehind = userProgress < parrotProgress;

  return (
    <div className="px-4 py-3">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Trip Progress
        </span>
        <span className={`text-xs font-bold ${isBehind ? 'text-amber-600' : 'text-emerald-600'}`}>
          {userProgress}%
        </span>
      </div>
      <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-emerald-400 z-10"
          style={{ left: `${parrotProgress}%` }}
        >
          <div className="absolute -top-1 -left-1.5 text-xs">🦜</div>
        </div>
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${
            isBehind
              ? 'bg-gradient-to-r from-amber-400 to-amber-500'
              : 'bg-gradient-to-r from-emerald-400 to-emerald-600'
          }`}
          style={{ width: `${userProgress}%` }}
        />
      </div>
      {isBehind && (
        <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
          <span>⚡</span> You're a bit behind! Catch up with the parrot!
        </p>
      )}
    </div>
  );
}
```

Key changes vs original:
- Props renamed: `currentPhaseOrder` → `completedCount`, `parrotPhaseOrder` → `parrotCompletedCount`
- Formula: `(completedCount / totalPhases) * 100` — no `+1`

- [ ] **Step 2: Verify build — will fail because HomeScreen still passes old prop names**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
npm run build 2>&1 | grep -E "error|Error" | head -10
```

Expected: TypeScript error about `currentPhaseOrder` not existing — that's correct, confirms the prop rename worked.

- [ ] **Step 3: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add frontend/src/shared/components/ProgressBar.tsx
git commit -m "fix: rename ProgressBar props to completedCount, remove +1 from formula"
```

---

## Task 2: Fix HomeScreen progress calculations

**Files:**
- Modify: `frontend/src/features/trip/pages/HomeScreen.tsx`

The current block (around lines 69–82) is:

```tsx
const currentUserPhaseId = travelers.find(t => t.id === user?.userId)?.current_phase_id ?? null;
const parrotPhaseId = computeParrotPhaseId(phases);

const tripStarted = tripInfo
  ? new Date(tripInfo.start_date + 'T00:00:00') <= new Date()
  : false;

const progressPhases = tripStarted
  ? phases.filter(p => p.phase_type === 'in-trip')
  : phases.filter(p => p.phase_type === 'pre-trip');

const currentUserIdx = progressPhases.findIndex(p => p.id === currentUserPhaseId);
const parrotIdx = progressPhases.findIndex(p => p.id === parrotPhaseId);
const totalPhases = progressPhases.length;
```

And the ProgressBar call is:
```tsx
<ProgressBar
  totalPhases={totalPhases}
  currentPhaseOrder={currentUserIdx}
  parrotPhaseOrder={parrotIdx}
/>
```

- [ ] **Step 1: Replace the progress calculation block**

Find the block above and replace it with:

```tsx
const currentUserPhaseId = travelers.find(t => t.id === user?.userId)?.current_phase_id ?? null;

const tripStarted = tripInfo
  ? new Date(tripInfo.start_date + 'T00:00:00') <= new Date()
  : false;

const progressPhases = tripStarted
  ? phases.filter(p => p.phase_type === 'in-trip')
  : phases.filter(p => p.phase_type === 'pre-trip');

const totalPhases = progressPhases.length;

// completedCount = number of phases completed before the current one.
// findIndex returns -1 when currentUserPhaseId is not in progressPhases
// (e.g. all pre-trip phases done → currentUserPhaseId points to an in-trip day).
// -1 means all phases in the current mode are complete → treat as totalPhases.
const rawUserIdx = progressPhases.findIndex(p => p.id === currentUserPhaseId);
const completedCount = rawUserIdx === -1 ? totalPhases : rawUserIdx;

// Parrot: count how many phases in progressPhases are already done/started.
// Pre-trip mode: parrot is always at the same position as the user (user drives it).
// In-trip mode: count phases whose starts_at <= now.
const now = new Date();
const parrotCompletedCount = tripStarted
  ? progressPhases.filter(p => p.starts_at && new Date(p.starts_at) <= now).length
  : completedCount;
```

- [ ] **Step 2: Update the ProgressBar call**

Find:
```tsx
<ProgressBar
  totalPhases={totalPhases}
  currentPhaseOrder={currentUserIdx}
  parrotPhaseOrder={parrotIdx}
/>
```

Replace with:
```tsx
<ProgressBar
  totalPhases={totalPhases}
  completedCount={completedCount}
  parrotCompletedCount={parrotCompletedCount}
/>
```

- [ ] **Step 3: Remove now-unused variables**

The variables `parrotPhaseId` and `computeParrotPhaseId` are still used in the game board (to show the parrot mascot on the correct tile), so keep them. But `parrotIdx` is no longer used — it was removed in Step 1. Verify no TypeScript errors remain about unused variables.

Check if `parrotPhaseId` and `computeParrotPhaseId` are still referenced in the game board JSX lower in the file:
- `const isParrotHere = phase.id === parrotPhaseId;` — YES, keep `parrotPhaseId`
- `computeParrotPhaseId(phases)` — keep the function and its call

So the only removal is `parrotIdx` (replaced by `parrotCompletedCount`).

- [ ] **Step 4: Verify build passes with no TypeScript errors**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
npm run build 2>&1 | tail -8
```

Expected: `✓ built in Xms` with no errors.

- [ ] **Step 5: Verify the math manually**

With the new logic:
- User with 0 phases done: `rawUserIdx = 0`, `completedCount = 0` → `0/total = 0%` ✅
- User with 2 of 4 done: `rawUserIdx = 2`, `completedCount = 2` → `2/4 = 50%` ✅
- User with all 4 done: `rawUserIdx = -1`, `completedCount = 4` → `4/4 = 100%` ✅
- User unmarks phase 2: backend returns phase 2 as current → `rawUserIdx = 2`, `completedCount = 2` → bar regresses ✅
- In-trip, 2 of 5 days started: `parrotCompletedCount = 2` → `2/5 = 40%` ✅

- [ ] **Step 6: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add frontend/src/features/trip/pages/HomeScreen.tsx
git commit -m "fix: use completedCount semantics for progress bar — starts at 0%, regresses on unmark, handles all-done edge case"
```

---

## Task 3: Deploy

- [ ] **Step 1: Deploy frontend**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
make deploy-frontend 2>&1 | tail -5
```

Expected:
```
Frontend URL: https://storage.googleapis.com/parrot-trips-frontend/index.html?v=<new-hash>
```

- [ ] **Step 2: Update URL in docs**

```bash
# Replace old hash with new hash in both docs (substitute <new-hash> with actual value):
sed -i '' 's/index\.html?v=aa14855/index.html?v=<new-hash>/g' \
  PRODUCT_AND_SYSTEM_DESIGN/15-deploy-gcp.md \
  PRODUCT_AND_SYSTEM_DESIGN/16-guia-demo.md

git add PRODUCT_AND_SYSTEM_DESIGN/15-deploy-gcp.md PRODUCT_AND_SYSTEM_DESIGN/16-guia-demo.md
git commit -m "docs: update frontend URL after progress bar fix"
```

---

## Self-review

**Spec coverage:**
- ✅ Bar starts at 0% for new users (completedCount = 0 when on first phase)
- ✅ Bar regresses when user unmarks a phase (backend returns earlier phase → smaller findIndex)
- ✅ Bar doesn't jump to 0% when all pre-trip phases done (rawUserIdx=-1 → completedCount=totalPhases → 100%)
- ✅ Parrot in pre-trip follows user (completedCount shared)
- ✅ Parrot in in-trip counts started days (filter starts_at <= now)
- ✅ Game board parrot position (parrotPhaseId) unchanged
- ✅ Deploy included

**Placeholder scan:** None. The sed command in Task 3 has `<new-hash>` as a placeholder — this is intentional and must be filled with the actual hash printed by `make deploy-frontend`.

**Type consistency:**
- `ProgressBar` props: `completedCount: number`, `parrotCompletedCount: number` — used identically in both files. ✅
- `rawUserIdx` is local to HomeScreen, never exported. ✅
- `parrotPhaseId` and `computeParrotPhaseId` kept for game board — no type change. ✅

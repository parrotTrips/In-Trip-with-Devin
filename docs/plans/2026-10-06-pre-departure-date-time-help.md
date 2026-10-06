# Pre-Departure Date, Time, and Help UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Give travelers calendar date inputs, five-minute time selects, and collapsed contextual help in the Pre Departure form.

**Architecture:** Add small form-control helpers inside the existing profile screen module, preserving the current API values (`YYYY-MM-DD` and `HH:mm`). Replace the three always-visible callouts with an accessible disclosure component located after its related field.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Vitest, Testing Library

---

### Task 1: Specify the new input and help behavior

**Files:**
- Modify: `frontend/src/features/profile/ProfileScreen.test.tsx`

**Step 1: Write the failing test**

Update the Pre Departure save test to assert that arrival/departure dates are
`type="date"`, arrival/departure times are selects with five-minute options, and
the three help messages are initially absent. Select values using
`userEvent.selectOptions`, expand each `More information` control, and assert the
associated help text appears after its field.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --run src/features/profile/ProfileScreen.test.tsx`

Expected: FAIL because the date/time controls and help disclosures do not exist.

### Task 2: Implement constrained date and time controls

**Files:**
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`
- Test: `frontend/src/features/profile/ProfileScreen.test.tsx`

**Step 1: Add minimal controls**

Implement a labeled native date field that passes through `YYYY-MM-DD`. Generate
time options in five-minute increments, format their labels in 12-hour time, and
preserve any existing off-grid time as an extra selected option.

**Step 2: Replace Pre Departure fields**

Use the new controls for Arrival Date, Arrival Time, Departure Date, and Departure
Time while retaining current labels, validation, grid layout, and state keys.

**Step 3: Run test to verify input behavior passes**

Run: `cd frontend && npm test -- --run src/features/profile/ProfileScreen.test.tsx`

Expected: Help assertions still fail, while date/time assertions pass.

### Task 3: Implement contextual help disclosures

**Files:**
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`
- Test: `frontend/src/features/profile/ProfileScreen.test.tsx`

**Step 1: Add the disclosure component**

Create an accessible `FieldHelp` component with local collapsed state, a real
button, `aria-expanded`, `aria-controls`, and an information callout shown only
when expanded.

**Step 2: Reposition the messages**

Place check-in help after Early Check-in Preference, Instagram help after
Instagram Handle, and hotel address help after Home Address.

**Step 3: Run focused tests**

Run: `cd frontend && npm test -- --run src/features/profile/ProfileScreen.test.tsx`

Expected: PASS.

### Task 4: Verify the frontend and commit

**Files:**
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`
- Modify: `frontend/src/features/profile/ProfileScreen.test.tsx`

**Step 1: Run full frontend tests**

Run: `cd frontend && npm test -- --run`

Expected: PASS with no failures.

**Step 2: Run lint and production build**

Run: `cd frontend && npm run lint`

Run: `cd frontend && npm run build`

Expected: both commands exit successfully.

**Step 3: Review the diff**

Run: `git diff --check && git diff --stat origin/homologacao..HEAD`

Expected: no whitespace errors and only intended plan/frontend changes.

**Step 4: Commit**

```bash
git add frontend/src/features/profile/ProfileScreen.test.tsx frontend/src/features/profile/pages/ProfileScreen.tsx docs/plans/2026-10-06-pre-departure-date-time-help.md
git commit -m "feat: improve pre-departure date and time inputs"
```

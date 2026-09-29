# Cancellation Policy Information Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the imported trip cancellation policy to the traveler `Information` screen.

**Architecture:** Reuse the existing `InformationScreen` collapsible section pattern. Load cancellation policy data with the existing `getMyCancellationPolicy()` API helper and render each row as a compact title/body block.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, MSW.

**Spec:** `docs/plans/2026-09-15-cancellation-policy-information-design.md`

## Global Constraints

- Do not add a new route or page.
- Put the section below `FAQ`.
- Use the existing `/me/cancellation-policy` endpoint and `getMyCancellationPolicy()` helper.
- Keep loading failures non-blocking, consistent with the existing `Information` screen.

---

### Task 1: Render Cancellation Policy on Information

**Files:**
- Modify: `frontend/src/features/team/InformationScreen.test.tsx`
- Modify: `frontend/src/features/team/pages/InformationScreen.tsx`

**Interfaces:**
- Consumes: `getMyCancellationPolicy(): Promise<{ cancellation_policy: CancellationPolicyItem[] }>`
- Produces: `InformationScreen` section titled `Cancellation Policy`

- [ ] **Step 1: Write the failing test**

Replace the existing negative cancellation policy test with one that returns one policy row, renders `InformationScreen`, opens `Cancellation Policy`, and asserts the title/body are visible.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- InformationScreen.test.tsx --run`

Expected: FAIL because the section is not rendered yet.

- [ ] **Step 3: Write minimal implementation**

Import `getMyCancellationPolicy` and `CancellationPolicyItem`, add component state, include the API call in `Promise.all`, add a row component, and render a `Cancellation Policy` `CollapsibleSection` below `FAQ`.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- InformationScreen.test.tsx --run`

Expected: PASS.

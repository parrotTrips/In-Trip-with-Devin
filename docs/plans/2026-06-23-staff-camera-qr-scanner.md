# Staff Camera QR Scanner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the staff manual QR scan flow with an activity-scoped camera scanner and remove the global staff QR tab.

**Architecture:** Keep the backend unchanged and reuse the existing activity scan endpoint. Add a small frontend camera scanner component that decodes QR payloads inside the selected activity panel, then calls the existing `scanActivityTraveler(activity.id, payload)` client.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, MSW, `html5-qrcode`.

---

### Task 1: Add Camera Scanner Dependency

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

**Step 1: Install dependency**

Run: `cd frontend && npm install html5-qrcode`

Expected: `package.json` and `package-lock.json` include `html5-qrcode`.

**Step 2: Verify dependency resolves**

Run: `cd frontend && npm run build`

Expected: TypeScript and Vite can resolve the package. The build may still fail later if implementation is incomplete; at this step it should pass before code changes.

**Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add staff qr scanner dependency"
```

### Task 2: Replace Manual Scanner With Camera-First Activity Panel

**Files:**
- Modify: `frontend/src/features/staff/pages/StaffScreen.tsx`
- Test: `frontend/src/features/staff/StaffScreen.test.tsx`

**Step 1: Write failing tests**

Update the staff screen tests to mock `html5-qrcode` and cover:

- no global `QR Scan` bottom tab;
- clicking `Scan Travelers` in an expanded activity shows a camera scanner panel;
- simulated decoded QR text posts to `/me/staff/activities/:activityId/checkins/scan`;
- success increments the activity check-in counter;
- duplicate scan does not increment the counter.

Run: `cd frontend && npm test -- StaffScreen --run`

Expected: tests fail because the UI still has the global QR tab and no camera scanner.

**Step 2: Implement scanner behavior**

In `StaffScreen.tsx`:

- remove `scanner` from the `Tab` type;
- remove `QrScannerTab`;
- remove the `QR Scan` item from the bottom nav;
- replace the manual-first `ActivityScanPanel` with a camera-first panel using `Html5Qrcode`;
- start scanning when the panel opens;
- use `{ facingMode: 'environment' }`;
- submit decoded text through `scanActivityTraveler(activity.id, decodedText)`;
- ignore new decoded values while `submitting` is true;
- stop and clear the scanner on close/unmount;
- keep manual fallback available when camera start fails or the user opens it.

**Step 3: Run focused tests**

Run: `cd frontend && npm test -- StaffScreen --run`

Expected: staff screen tests pass.

**Step 4: Commit**

```bash
git add frontend/src/features/staff/pages/StaffScreen.tsx frontend/src/features/staff/StaffScreen.test.tsx
git commit -m "feat: scan travelers by camera inside staff activities"
```

### Task 3: Verify Frontend Build

**Files:**
- Read: `frontend/dist`

**Step 1: Run full frontend verification**

Run: `cd frontend && npm test -- --run && npm run build`

Expected: all frontend tests pass and production build succeeds.

**Step 2: Commit if verification requires fixes**

If fixes are needed, commit only the relevant files:

```bash
git add frontend/src/features/staff/pages/StaffScreen.tsx frontend/src/features/staff/StaffScreen.test.tsx frontend/package.json frontend/package-lock.json
git commit -m "fix: stabilize staff camera qr scanner"
```

### Task 4: Deploy and Validate Production

**Files:**
- Read: `frontend/dist`

**Step 1: Deploy frontend**

Run from `frontend`:

```bash
VITE_API_URL=https://parrot-trips-backend-428743191336.southamerica-east1.run.app netlify deploy --prod --dir=dist --site=e5840ec7-de34-4fbb-a115-ccf7e3292999
```

Expected: Netlify returns the production URL.

**Step 2: Validate bundle backend URL**

Run: `rg "localhost:8000|parrot-trips-backend" frontend/dist`

Expected: the production backend URL is present and `localhost:8000` is absent.

**Step 3: Push**

Run: `git push origin main`

Expected: remote `main` includes the scanner changes.

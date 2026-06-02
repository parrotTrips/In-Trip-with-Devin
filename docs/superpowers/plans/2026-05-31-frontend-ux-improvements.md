# Frontend UX Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 UX issues: blank initial screen, remove stale "Mark Day as Completed" button, add logout button to ProfileScreen, and replace the native date-of-birth picker with a 3-dropdown selector.

**Architecture:** All changes are isolated to the frontend React app. No backend changes required. Each task touches 1-2 files and can be implemented and deployed independently.

**Tech Stack:** React 18, TypeScript, React Router v7, Tailwind CSS, Lucide React icons

---

## File Map

| File | Action | What changes |
|---|---|---|
| `frontend/src/app/router.tsx` | Modify | Add catch-all `<Navigate to="/" />` to fix blank screen |
| `frontend/src/features/trip/pages/DayDetails.tsx` | Modify | Remove "Mark Day as Completed" button, state and API calls |
| `frontend/src/features/profile/pages/ProfileScreen.tsx` | Modify | Add logout button; replace DOB `<input type="date">` with 3-dropdown `DateSelectField` component |

---

## Task 1: Fix blank initial screen

**Files:**
- Modify: `frontend/src/app/router.tsx`

The app shows a blank screen on first load when the path is not exactly `/`. Adding a catch-all `<Navigate>` ensures any unknown path redirects to the Map screen.

- [ ] **Step 1: Update `router.tsx`**

Replace the entire file content at `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend/src/app/router.tsx`:

```tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import DayDetails from '../features/trip/pages/DayDetails';
import HomeScreen from '../features/trip/pages/HomeScreen';
import ProfileScreen from '../features/profile/pages/ProfileScreen';
import PhaseDetails from '../features/trip/pages/PhaseDetails';
import BottomNav from '../shared/components/BottomNav';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <div className="max-w-lg mx-auto relative min-h-screen bg-white shadow-xl">
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/phase/:phaseId" element={<PhaseDetails />} />
          <Route path="/day/:dayId" element={<DayDetails />} />
          <Route path="/profile" element={<ProfileScreen />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}
```

- [ ] **Step 2: Verify build passes**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
npm run build 2>&1 | tail -5
```

Expected: `✓ built in Xms`

- [ ] **Step 3: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add frontend/src/app/router.tsx
git commit -m "fix: redirect unknown paths to home to prevent blank screen"
```

---

## Task 2: Remove "Mark Day as Completed" button from DayDetails

**Files:**
- Modify: `frontend/src/features/trip/pages/DayDetails.tsx`

The in-trip phase completion is now automatic (date-based). The manual button is confusing and should be removed entirely along with its state and API calls.

- [ ] **Step 1: Update the imports at the top of `DayDetails.tsx`**

Remove `CheckCircle2`, `Circle`, `getPhaseCompletions`, `updatePhaseCompletion` from the imports. The file is at `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend/src/features/trip/pages/DayDetails.tsx`.

Replace the import block (lines 1-24) with:

```tsx
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  MapPin,
  Star,
  ChevronRight,
  Camera,
  Check,
  DollarSign,
  ImagePlus,
} from 'lucide-react';
import { useTripContext } from '../../../app/providers/trip-context';
import {
  getMyTripPhaseDetail,
  type Activity,
  type TripPhaseDetail,
} from '../services/trip-api';
```

- [ ] **Step 2: Update the `DayDetails` component — remove isCompleted state and handler**

In the `DayDetails` function body, remove:
- `const { user } = useAuth();` (the `useAuth` import too, since it's no longer used)
- `const [isCompleted, setIsCompleted] = useState(false);`
- The entire second `useEffect` block that calls `getPhaseCompletions`
- The entire `handleToggleCompleted` function

The component state section should look like this after the change:

```tsx
export default function DayDetails() {
  const { dayId } = useParams<{ dayId: string }>();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { tripInfo: _tripInfo } = useTripContext();

  const [phase, setPhase] = useState<TripPhaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dayId) return;
    setLoading(true);
    setError(null);
    getMyTripPhaseDetail(dayId)
      .then(data => setPhase(data))
      .catch(e => setError(e instanceof Error ? e.message : 'Erro ao carregar dia'))
      .finally(() => setLoading(false));
  }, [dayId]);
```

Note: keep the `useTripContext` import since `TripProvider` still wraps this component — just remove the usage. Actually, since `tripInfo` is no longer used at all in this component, remove the `useTripContext` import and usage entirely:

```tsx
export default function DayDetails() {
  const { dayId } = useParams<{ dayId: string }>();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [phase, setPhase] = useState<TripPhaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dayId) return;
    setLoading(true);
    setError(null);
    getMyTripPhaseDetail(dayId)
      .then(data => setPhase(data))
      .catch(e => setError(e instanceof Error ? e.message : 'Erro ao carregar dia'))
      .finally(() => setLoading(false));
  }, [dayId]);
```

- [ ] **Step 3: Remove the button from the JSX**

Find and remove the entire `<div className="px-4 pb-5">` block that contains the `handleToggleCompleted` button (lines 210-225 in the original). It looks like:

```tsx
        <div className="px-4 pb-5">
          <button
            onClick={handleToggleCompleted}
            className={`w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${
              isCompleted
                ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30'
                : 'bg-white/15 text-white border border-white/30 hover:bg-white/25'
            }`}
          >
            {isCompleted ? (
              <><CheckCircle2 size={18} /> Day Completed!</>
            ) : (
              <><Circle size={18} /> Mark Day as Completed</>
            )}
          </button>
        </div>
```

Remove this entire block.

- [ ] **Step 4: Verify build passes with no TypeScript errors**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
npm run build 2>&1 | tail -10
```

Expected: `✓ built in Xms` with no errors. If there are TS errors about unused imports, remove those imports.

- [ ] **Step 5: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add frontend/src/features/trip/pages/DayDetails.tsx
git commit -m "feat: remove Mark Day as Completed button — progress is now date-driven"
```

---

## Task 3: Add logout button to ProfileScreen

**Files:**
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`

The `AuthProvider` already exposes a `logout()` function via `useAuth()`. We just need to call it from the ProfileScreen and add a "Sign Out" button below the Save button.

- [ ] **Step 1: Add `logout` to the useAuth destructure**

In `ProfileScreen.tsx`, find:

```tsx
  const { user } = useAuth();
```

Replace with:

```tsx
  const { user, logout } = useAuth();
```

- [ ] **Step 2: Add the LogOut icon to imports**

Find the lucide-react import line at the top of the file:

```tsx
import { ArrowLeft, User, FileText, ChevronDown, ChevronUp, Save, Loader2, ShoppingCart, ExternalLink } from 'lucide-react';
```

Replace with:

```tsx
import { ArrowLeft, User, FileText, ChevronDown, ChevronUp, Save, Loader2, ShoppingCart, ExternalLink, LogOut } from 'lucide-react';
```

- [ ] **Step 3: Add the logout button below the Save button**

Find the fixed bottom bar section (the `<div className="fixed bottom-16 ...">` block). It currently ends with the Save button. Add a logout button after the Save button's closing `</button>` tag, still inside the `max-w-lg` div:

```tsx
      {/* Save button - fixed at bottom */}
      <div className="fixed bottom-16 left-0 right-0 px-4 pb-4 z-40">
        <div className="max-w-lg mx-auto space-y-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className={`w-full py-3.5 rounded-2xl font-semibold text-sm flex items-center justify-center gap-2 shadow-lg transition-all ${
              saveError
                ? 'bg-red-500 text-white'
                : saved
                ? 'bg-emerald-500 text-white'
                : 'bg-emerald-700 hover:bg-emerald-800 text-white'
            }`}
          >
            {saving ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Saving...
              </>
            ) : saveError ? (
              <>
                <Save size={18} />
                Error saving — try again
              </>
            ) : saved ? (
              <>
                <Save size={18} />
                Saved!
              </>
            ) : (
              <>
                <Save size={18} />
                Save Profile
              </>
            )}
          </button>

          <button
            onClick={logout}
            className="w-full py-3 rounded-2xl font-semibold text-sm flex items-center justify-center gap-2 text-red-500 bg-red-50 hover:bg-red-100 transition-colors"
          >
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </div>
```

Note the key changes vs the original: the outer div now uses `space-y-2` instead of no spacing, and the inner `max-w-lg` div wraps both buttons.

- [ ] **Step 4: Verify build passes**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
npm run build 2>&1 | tail -5
```

Expected: `✓ built in Xms`

- [ ] **Step 5: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add frontend/src/features/profile/pages/ProfileScreen.tsx
git commit -m "feat: add Sign Out button to ProfileScreen"
```

---

## Task 4: Replace date-of-birth picker with 3-dropdown selector

**Files:**
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`

Replace the `<InputField>` for `dob` (Date of Birth) with a new inline `DateSelectField` component using three `<select>` dropdowns: Day, Month, Year. The Year dropdown lists years from current year down to 1930 in descending order. This stores the value in `YYYY-MM-DD` format, consistent with what the backend expects.

The passport date fields (`passport_issue_date`, `passport_expiration_date`) keep the native `<input type="date">` since they are near-present dates where the native picker works well.

- [ ] **Step 1: Add the `DateSelectField` component to `ProfileScreen.tsx`**

Add this new component after the `TextAreaField` component definition (before `export default function ProfileScreen()`):

```tsx
function DateSelectField({ label, value, onChange }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: currentYear - 1929 }, (_, i) => currentYear - i);
  const months = [
    { value: '01', label: 'January' },
    { value: '02', label: 'February' },
    { value: '03', label: 'March' },
    { value: '04', label: 'April' },
    { value: '05', label: 'May' },
    { value: '06', label: 'June' },
    { value: '07', label: 'July' },
    { value: '08', label: 'August' },
    { value: '09', label: 'September' },
    { value: '10', label: 'October' },
    { value: '11', label: 'November' },
    { value: '12', label: 'December' },
  ];

  // Parse existing YYYY-MM-DD value
  const parts = value ? value.split('-') : ['', '', ''];
  const selectedYear = parts[0] ?? '';
  const selectedMonth = parts[1] ?? '';
  const selectedDay = parts[2] ?? '';

  const daysInMonth = selectedYear && selectedMonth
    ? new Date(parseInt(selectedYear), parseInt(selectedMonth), 0).getDate()
    : 31;
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  const handleChange = (year: string, month: string, day: string) => {
    if (year && month && day) {
      const paddedDay = day.padStart(2, '0');
      onChange(`${year}-${month}-${paddedDay}`);
    } else {
      onChange('');
    }
  };

  const selectClass = "px-2 py-2 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all bg-white";

  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-500">{label}</label>
      <div className="grid grid-cols-3 gap-2">
        <select
          value={selectedDay}
          onChange={e => handleChange(selectedYear, selectedMonth, e.target.value)}
          className={selectClass}
        >
          <option value="">Day</option>
          {days.map(d => (
            <option key={d} value={String(d).padStart(2, '0')}>{d}</option>
          ))}
        </select>
        <select
          value={selectedMonth}
          onChange={e => handleChange(selectedYear, e.target.value, selectedDay)}
          className={selectClass}
        >
          <option value="">Month</option>
          {months.map(m => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
        <select
          value={selectedYear}
          onChange={e => handleChange(e.target.value, selectedMonth, selectedDay)}
          className={selectClass}
        >
          <option value="">Year</option>
          {years.map(y => (
            <option key={y} value={String(y)}>{y}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Replace the DOB InputField with DateSelectField**

Find this line in the Registration Details section:

```tsx
              <InputField label="Date of Birth" value={form.dob} onChange={v => setField('dob', v)} type="date" />
```

Replace it with:

```tsx
              <DateSelectField label="Date of Birth" value={form.dob} onChange={v => setField('dob', v)} />
```

- [ ] **Step 3: Verify build passes**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
npm run build 2>&1 | tail -5
```

Expected: `✓ built in Xms`

- [ ] **Step 4: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add frontend/src/features/profile/pages/ProfileScreen.tsx
git commit -m "feat: replace date-of-birth native picker with 3-dropdown selector"
```

---

## Task 5: Deploy

- [ ] **Step 1: Deploy frontend to Cloud Storage**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
make deploy-frontend
```

Expected output ends with:
```
Frontend URL: https://storage.googleapis.com/parrot-trips-frontend/index.html?v=<new-hash>
```

- [ ] **Step 2: Update frontend URL in demo guide**

In `PRODUCT_AND_SYSTEM_DESIGN/16-guia-demo.md`, replace all occurrences of the old `?v=` hash with the new one printed by `make deploy-frontend`.

- [ ] **Step 3: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add PRODUCT_AND_SYSTEM_DESIGN/16-guia-demo.md
git commit -m "docs: update frontend URL after UX improvements deploy"
```

---

## Self-review

**Spec coverage:**
- ✅ Blank initial screen → `<Navigate to="/" replace />` catch-all in router
- ✅ Remove "Mark Day as Completed" → button, state, and API calls removed from DayDetails
- ✅ Logout button → Sign Out button in ProfileScreen calling `logout()` from `useAuth`
- ✅ Better date picker for DOB → `DateSelectField` with Day/Month/Year dropdowns, Year from current down to 1930
- ✅ Deploy step included

**Placeholder scan:** None found.

**Type consistency:**
- `DateSelectField` receives `{ label: string; value: string; onChange: (v: string) => void }` — same signature as `InputField`, drop-in replacement. ✅
- `logout` comes from `useAuth()` which is already typed in `auth-context.ts`. ✅
- `DayDetails` no longer imports `useAuth` or trip-api completion functions — no dangling references. ✅

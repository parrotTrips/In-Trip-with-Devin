# Multi-Trip Login Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let one phone-authenticated person safely select and switch among current/future trips, with a traveler or staff role derived independently for each trip.

**Architecture:** OTP verification resolves eligible `trip_travelers` memberships and either issues a trip-scoped session token or a short-lived selection token. All application routes consume the selected `trip_id` from the session and validate membership; `trip_staff` determines the effective role. React stores the active trip in auth state and inserts a trip picker between OTP login and the role-specific application.

**Tech Stack:** FastAPI, SQLAlchemy async, PostgreSQL, python-jose JWT, Pytest, React 18, TypeScript, React Router, Vitest, Testing Library, MSW.

---

### Task 1: Centralize eligible-trip lookup and per-trip role resolution

**Files:**
- Create: `backend/app/services/trip_membership_service.py`
- Create: `backend/tests/services/test_trip_membership_service.py`

**Step 1: Write failing membership tests**

Seed `wetravel_trips`, `trip_travelers`, and `trip_staff` rows covering an ended trip, a current trip, two future trips, traveler-only membership, and staff membership. Assert that the result excludes the ended trip, places the current trip first, sorts future trips by `start_date`, and calculates the role from `trip_staff` rather than `users.role`.

```python
trips = await list_eligible_trips(str(user.id), session)
assert [trip["trip_id"] for trip in trips] == ["CURRENT", "FUTURE-1", "FUTURE-2"]
assert [trip["role"] for trip in trips] == ["traveler", "staff", "traveler"]
```

Also test `get_eligible_trip_membership(user_id, trip_id, session)` returns `None` for ended and unrelated trips.

**Step 2: Run the tests and verify failure**

Run: `cd backend && poetry run pytest tests/services/test_trip_membership_service.py -v`

Expected: FAIL because `trip_membership_service` does not exist.

**Step 3: Implement the shared query**

Create these functions:

```python
async def list_eligible_trips(user_id: str, session: AsyncSession) -> list[dict]:
    # Join trip_travelers -> wetravel_trips, left join trip_staff for the same
    # user and trip. Filter end_date >= CURRENT_DATE or NULL. Return trip_id,
    # title, destination, start_date, end_date, role, and is_current.

async def get_eligible_trip_membership(
    user_id: str, trip_id: str, session: AsyncSession
) -> dict | None:
    # Reuse the same eligibility and role rules, narrowed to trip_id.
```

Use `CASE WHEN ts.id IS NULL THEN 'traveler' ELSE 'staff' END AS role` and order current trips before future trips, then `start_date NULLS LAST`.

**Step 4: Run the tests**

Run: `cd backend && poetry run pytest tests/services/test_trip_membership_service.py -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/services/trip_membership_service.py backend/tests/services/test_trip_membership_service.py
git commit -m "feat(auth): resolve eligible trips and per-trip roles"
```

### Task 2: Add selection and trip-scoped token contracts

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/routers/auth.py`
- Modify: `backend/tests/services/test_auth_service.py`
- Create: `backend/tests/routers/test_auth_trip_selection.py`

**Step 1: Write failing service tests for all OTP outcomes**

Replace the old assumption that every successful OTP returns a global-role token. Cover:

```python
assert no_trips["status"] == "no_trips"
assert one_trip["status"] == "trip_selected"
assert one_trip["active_trip"]["trip_id"] == "TRIP-A"
assert many_trips["status"] == "selection_required"
assert len(many_trips["trips"]) == 2
assert "selection_token" in many_trips
```

Decode tokens and assert selection tokens have `token_type="trip_selection"` with no `trip_id`, while session tokens have `token_type="session"`, `trip_id`, and the derived role.

**Step 2: Run the focused tests and verify failure**

Run: `cd backend && poetry run pytest tests/services/test_auth_service.py -v`

Expected: FAIL because the response and token claims still use the global role.

**Step 3: Implement typed token issuance and OTP branching**

Add `JWT_SELECTION_EXPIRY_MINUTES` with a short default such as 15 minutes. Replace `_create_access_token` with explicit helpers:

```python
def _create_selection_token(user_id: str, phone: str) -> str:
    return _encode({"sub": user_id, "phone": phone, "token_type": "trip_selection"}, minutes=15)

def _create_session_token(user_id: str, phone: str, trip_id: str, role: str) -> str:
    return _encode({
        "sub": user_id, "phone": phone, "token_type": "session",
        "trip_id": trip_id, "role": role,
    }, days=JWT_EXPIRY_DAYS)
```

After consuming the OTP, call `list_eligible_trips` and return the approved `no_trips`, `trip_selected`, or `selection_required` shape.

Add `TripSelectionRequest` to `backend/app/schemas/auth.py`:

```python
class TripSelectionRequest(BaseModel):
    trip_id: str
```

**Step 4: Write failing route tests for listing and selecting**

Test:

- `GET /auth/trips` accepts selection and session tokens;
- `POST /auth/select-trip` returns a scoped token for an eligible membership;
- selecting another person's or an ended trip returns 403;
- expired or wrong-type tokens return 401;
- role comes from `trip_staff` for the selected trip.

**Step 5: Implement auth token extraction and routes**

Do not rely on the application middleware for `/auth`. Add a small private decoder in the auth router/service that reads `Authorization: Bearer ...`, validates `token_type in {trip_selection, session}`, and extracts `sub` and `phone`.

```python
@router.get("/trips")
async def list_my_trips(request: Request, session=Depends(get_db_session)):
    identity = decode_trip_choice_identity(request)
    return {"trips": await list_eligible_trips(identity.user_id, session)}

@router.post("/select-trip")
async def select_trip(req: TripSelectionRequest, request: Request, session=Depends(get_db_session)):
    identity = decode_trip_choice_identity(request)
    membership = await get_eligible_trip_membership(identity.user_id, req.trip_id, session)
    if membership is None:
        raise HTTPException(status_code=403, detail="Trip not available")
    return session_payload(identity, membership)
```

**Step 6: Run backend auth tests**

Run: `cd backend && poetry run pytest tests/services/test_auth_service.py tests/routers/test_auth_trip_selection.py -v`

Expected: PASS.

**Step 7: Commit**

```bash
git add backend/app/core/config.py backend/app/schemas/auth.py backend/app/services/auth_service.py backend/app/routers/auth.py backend/tests/services/test_auth_service.py backend/tests/routers/test_auth_trip_selection.py
git commit -m "feat(auth): issue trip selection and scoped session tokens"
```

### Task 3: Enforce scoped sessions in middleware and staff authorization

**Files:**
- Modify: `backend/app/middleware/auth.py`
- Modify: `backend/app/routers/staff.py`
- Create: `backend/tests/middleware/test_auth.py`
- Modify: `backend/tests/test_staff_api.py` (or the existing staff router test file found during implementation)

**Step 1: Write failing middleware tests**

Assert protected routes reject selection tokens and legacy tokens without `trip_id`, while a valid session token populates:

```python
request.state.user_id
request.state.phone
request.state.trip_id
request.state.role
```

Expect 401 with a stable detail such as `Trip session required` for the invalid token types.

**Step 2: Run and verify failure**

Run: `cd backend && poetry run pytest tests/middleware/test_auth.py -v`

Expected: FAIL because middleware currently accepts any JWT containing `sub` and `phone`.

**Step 3: Tighten middleware claims**

Require `token_type == "session"`, non-empty `trip_id`, and `role in {"traveler", "staff"}` on protected app routes. Copy the four claims to request state. Keep `/auth`, `/admin`, and health paths behavior unchanged.

**Step 4: Write failing staff authorization tests**

Cover a person who is staff on trip A and traveler on trip B. A trip-A token may access staff routes; a trip-B token receives 403. Removing their `trip_staff` row after token issuance must also produce 403.

**Step 5: Replace global staff resolution**

Replace `_get_staff_trip_uuid(user_id, session)` with:

```python
async def _require_staff_membership(user_id: str, trip_id: str, session: AsyncSession) -> str:
    exists = await session.scalar(select(TripStaff.id).where(
        TripStaff.user_id == uuid.UUID(user_id),
        TripStaff.wetravel_trip_uuid == trip_id,
    ))
    if exists is None:
        raise HTTPException(status_code=403, detail="Staff access required")
    return trip_id
```

Every staff handler passes `request.state.trip_id`. Remove authorization checks against `users.role`. Where staff lists travelers, filter by `trip_travelers` membership rather than `users.role`, because another trip's staff member can still be a traveler in the selected trip.

**Step 6: Run middleware and staff tests**

Run: `cd backend && poetry run pytest tests/middleware/test_auth.py tests -k staff -v`

Expected: PASS.

**Step 7: Commit**

```bash
git add backend/app/middleware/auth.py backend/app/routers/staff.py backend/tests
git commit -m "fix(auth): enforce selected trip and per-trip staff access"
```

### Task 4: Scope every traveler API to the authenticated trip

**Files:**
- Modify: `backend/app/routers/trip.py`
- Modify: `backend/app/routers/profile.py`
- Modify: `backend/app/services/trip_service.py`
- Modify: `backend/app/services/profile_service.py`
- Modify: `backend/app/services/checklist_service.py`
- Modify: relevant tests under `backend/tests/services/`
- Create: `backend/tests/routers/test_trip_scope.py`

**Step 1: Write cross-trip isolation tests**

Seed one user on trips A and B with distinct phases, announcements, QR identities, travelers, profiles, checklist progress, contacts, recommendations, FAQ, and feedback. Using a trip-B session token, assert every `/me/...` response contains only trip-B data. Attempt IDs belonging to trip A on detail/update routes and expect 404 or 403.

**Step 2: Run isolation tests and verify failure**

Run: `cd backend && poetry run pytest tests/routers/test_trip_scope.py -v`

Expected: FAIL because routes currently select the first active trip or accept caller-supplied trip IDs.

**Step 3: Replace implicit trip lookup in trip routes**

Use `request.state.trip_id` in `get_my_trip`, QR, phases, phase detail, traveler list, announcements, team, contacts, recommendations, FAQ, cancellation policy, feedback, and related handlers. Replace `_get_traveler_trip_uuid` and `_get_active_trip_traveler` with helpers requiring both user and selected trip:

```python
async def _get_trip_traveler(user_id: str, trip_id: str, session: AsyncSession) -> TripTraveler:
    membership = await session.scalar(select(TripTraveler).where(
        TripTraveler.user_id == uuid.UUID(user_id),
        TripTraveler.wetravel_trip_uuid == trip_id,
    ))
    if membership is None:
        raise HTTPException(status_code=403, detail="Trip membership required")
    return membership
```

Change service signatures to accept `trip_id` explicitly, for example `get_trip_phases(user_id, trip_id, session)` and always constrain phase/activity IDs to that trip.

**Step 4: Scope profile and checklist routes**

Ignore or remove public caller control of `trip_id` for authenticated self-service routes. Pass `request.state.trip_id` into profile and checklist services and verify the `TripTraveler` belongs to both the authenticated user and selected trip.

**Step 5: Run service and router tests**

Run: `cd backend && poetry run pytest tests/services tests/routers/test_trip_scope.py -v`

Expected: PASS.

**Step 6: Search for residual implicit selection**

Run: `rg -n "ORDER BY wt.start_date.*|LIMIT 1|users.role|User.role" backend/app/routers backend/app/services`

Expected: no authentication/authorization path chooses a person's trip with `LIMIT 1` or uses `users.role`; document any unrelated display-only match.

**Step 7: Commit**

```bash
git add backend/app/routers backend/app/services backend/tests
git commit -m "fix(api): isolate traveler data by selected trip"
```

### Task 5: Expand frontend auth state and API types

**Files:**
- Modify: `frontend/src/features/auth/services/auth-api.ts`
- Modify: `frontend/src/app/providers/auth-context.ts`
- Modify: `frontend/src/app/providers/AuthProvider.tsx`
- Modify: `frontend/src/shared/api/client.ts`
- Modify: `frontend/src/app/providers/AuthProvider.test.tsx`

**Step 1: Write failing auth-provider tests**

Cover storing a trip-scoped authenticated user, holding a pending selection session, atomically replacing the session during trip switch, and clearing legacy `parrot_user` data that has no `tripId`.

**Step 2: Run and verify failure**

Run: `cd frontend && npm test -- --run src/app/providers/AuthProvider.test.tsx`

Expected: FAIL because auth state has no active trip or pending-selection state.

**Step 3: Add shared response and state types**

Define:

```ts
export interface TripChoice {
  trip_id: string;
  title: string;
  destination: string | null;
  start_date: string | null;
  end_date: string | null;
  role: 'traveler' | 'staff';
  is_current: boolean;
}

export type VerifyOTPResult =
  | { status: 'no_trips'; user_id: string; phone: string; name: string | null }
  | { status: 'selection_required'; user_id: string; phone: string; name: string | null; selection_token: string; trips: TripChoice[] }
  | { status: 'trip_selected'; user_id: string; phone: string; name: string | null; access_token: string; active_trip: TripChoice };
```

Add `listTrips(token)` and `selectTrip(token, tripId)` API calls. Extend `AuthUser` with `tripId`, `activeTrip`, and its per-trip `role`. Add pending-selection state and context actions `beginTripSelection`, `completeTripSelection`, `openTripSwitcher`, and `cancelTripSwitcher` (exact names may be simplified, but preserve the state transitions).

**Step 4: Make token use explicit in the API client**

Ensure ordinary app requests use the current scoped session token. Auth selection calls pass their supplied selection/session token directly and do not accidentally read a stale localStorage value.

**Step 5: Run auth tests and type-check**

Run: `cd frontend && npm test -- --run src/app/providers/AuthProvider.test.tsx && npm run build`

Expected: PASS.

**Step 6: Commit**

```bash
git add frontend/src/features/auth/services/auth-api.ts frontend/src/app/providers frontend/src/shared/api/client.ts
git commit -m "feat(frontend): model selected trip authentication state"
```

### Task 6: Build the post-OTP trip selector and no-trip state

**Files:**
- Create: `frontend/src/features/auth/pages/TripSelectorScreen.tsx`
- Create: `frontend/src/features/auth/TripSelectorScreen.test.tsx`
- Modify: `frontend/src/features/auth/pages/LoginScreen.tsx`
- Modify: `frontend/src/features/auth/LoginScreen.test.tsx`
- Modify: `frontend/src/app/App.tsx`
- Modify: `frontend/src/app/App.test.tsx`

**Step 1: Write failing login flow tests**

With MSW, test the three `verify-otp` results:

- `trip_selected` calls the scoped login action and enters the app;
- `selection_required` renders the selector without entering the app;
- `no_trips` renders an explanatory state with a sign-out/back action.

**Step 2: Run and verify failure**

Run: `cd frontend && npm test -- --run src/features/auth/LoginScreen.test.tsx src/app/App.test.tsx`

Expected: FAIL because login assumes one legacy response shape.

**Step 3: Implement OTP state branching**

Update `handleVerifyCode` to switch on `result.status`. Do not store a selection token as a normal logged-in app session.

**Step 4: Write failing selector component tests**

Assert current trips render before future trips, staff badges appear only where appropriate, date/destination data is visible, double selection is disabled while loading, API errors remain on the selector, and successful selection enters the correct role.

**Step 5: Implement the selector**

Build accessible trip cards/buttons consistent with the existing emerald Parrot visual language. On click, call `selectTrip`, then complete the scoped session. Include loading, retryable error, empty, and single-trip informational states.

**Step 6: Gate application rendering**

In `AppContent`, render in this order: OTP login, no-trip state, trip selector, staff/traveler app. Key the role-specific app subtree by `user.tripId` so changing trips remounts providers and clears cached trip state.

**Step 7: Run tests and build**

Run: `cd frontend && npm test -- --run src/features/auth/TripSelectorScreen.test.tsx src/features/auth/LoginScreen.test.tsx src/app/App.test.tsx && npm run build`

Expected: PASS.

**Step 8: Commit**

```bash
git add frontend/src/features/auth frontend/src/app/App.tsx frontend/src/app/App.test.tsx
git commit -m "feat(frontend): add post-OTP trip selection"
```

### Task 7: Add in-app trip switching for traveler and staff views

**Files:**
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`
- Modify: `frontend/src/features/profile/ProfileScreen.test.tsx`
- Modify: `frontend/src/features/staff/pages/StaffScreen.tsx`
- Modify: `frontend/src/features/staff/StaffScreen.test.tsx`
- Modify: `frontend/src/app/App.tsx`
- Modify: `frontend/src/app/providers/TripProvider.tsx`

**Step 1: Write failing traveler switch tests**

Assert `Trocar de viagem` appears in the traveler profile, refreshes `/auth/trips`, opens the selector without OTP, and preserves the existing session if the person cancels or selection fails.

**Step 2: Write failing staff switch tests**

Assert the staff header/menu offers the same action. Selecting a traveler-role trip leaves staff UI and enters traveler UI; selecting a staff-role trip enters staff UI. The existing same-trip traveler preview remains unchanged.

**Step 3: Run and verify failures**

Run: `cd frontend && npm test -- --run src/features/profile/ProfileScreen.test.tsx src/features/staff/StaffScreen.test.tsx`

Expected: FAIL because only sign-out and view switching exist.

**Step 4: Implement trip switching**

Call `listTrips(user.token)` when opening the switcher. Keep the current authenticated session available for cancel/retry. After successful selection, replace `user.token`, `tripId`, `activeTrip`, and `role` together. Reset staff traveler-preview state whenever `tripId` changes.

Ensure `TripProvider` remounts/refetches and analytics unregister the old `viagem_id` before registering the new one.

**Step 5: Run frontend tests and build**

Run: `cd frontend && npm test -- --run src/features/profile/ProfileScreen.test.tsx src/features/staff/StaffScreen.test.tsx src/app/App.test.tsx src/app/posthog-tracking.test.tsx && npm run build`

Expected: PASS.

**Step 6: Commit**

```bash
git add frontend/src/features/profile frontend/src/features/staff frontend/src/app
git commit -m "feat(frontend): switch active trips without new OTP"
```

### Task 8: Audit import compatibility and complete end-to-end verification

**Files:**
- Modify: `backend/scripts/import_staff_content.py` if tests reveal missing reuse/link behavior
- Modify: the traveler import service/script responsible for `users` and `trip_travelers`
- Modify: corresponding backend tests
- Create: `backend/scripts/audit_multi_trip_memberships.py`
- Modify: `docs/guia-interno-parrot-app.md`

**Step 1: Add failing import regression tests**

Cover the same normalized phone imported as traveler on trip A and staff on trip B. Assert one `users` row, two `trip_travelers` rows, and a `trip_staff` row only for trip B. Cover repeated imports as idempotent.

**Step 2: Run and verify tests**

Run the specific import test modules discovered beside `backend/scripts/import_staff_content.py` and the traveler importer.

Expected: either PASS, proving compatibility already exists, or FAIL with the concrete duplicate/missing-link behavior.

**Step 3: Apply only necessary import fixes**

Normalize phone numbers consistently before lookup, reuse `users.id`, upsert `(wetravel_trip_uuid, user_id)` memberships, and never overwrite a global role as an authorization decision. Keep `users.role` writes only if a legacy path still requires them during rollout.

**Step 4: Add a read-only audit script**

The script reports, without mutating data:

- duplicate normalized phones;
- `trip_staff` rows missing matching `trip_travelers` rows;
- memberships whose trip is absent from `wetravel_trips`;
- users with multiple eligible trips and their derived roles.

Require an explicit database URL and print counts plus affected IDs/phones. Add a test for its query/report formatting if practical.

**Step 5: Document operations and rollout**

Update the internal guide with the OTP outcomes, selector behavior, role derivation, audit command, legacy-session clearing behavior, and rollback note.

**Step 6: Run full verification**

Run:

```bash
cd backend && poetry run pytest -v
cd frontend && npm test -- --run
cd frontend && npm run lint
cd frontend && npm run build
```

Expected: all commands exit 0. Review any pre-existing unrelated lint/test failure separately; do not conceal it.

**Step 7: Perform final security searches**

Run:

```bash
rg -n "users\.role|User\.role|request\.state\.trip_id|LIMIT 1" backend/app/routers backend/app/services
rg -n "parrot_user|tripId|selection_token|Trocar de viagem" frontend/src
```

Expected: every authenticated trip-data path is scoped by `request.state.trip_id`; remaining global-role references are admin/display compatibility only and are documented.

**Step 8: Commit**

```bash
git add backend/scripts backend/tests docs/guia-interno-parrot-app.md
git commit -m "chore: audit and document multi-trip memberships"
```

### Task 9: Manual acceptance pass

**Files:**
- Modify only if a defect is found, with a failing regression test first.

**Step 1: Prepare acceptance identities**

Create or identify test accounts for: one-trip traveler, multi-trip traveler, multi-trip staff, and mixed traveler/staff roles.

**Step 2: Exercise the approved flows**

Verify OTP auto-entry for one trip, selection for multiple trips, current/future filtering, staff default entry, same-trip traveler preview, cross-trip role change, switch without OTP, and sign out.

**Step 3: Verify isolation in browser network responses**

Switch between trips with visibly different itinerary/team/announcement data and confirm no previous-trip response remains rendered. Confirm the new bearer token changes and contains the selected `trip_id`.

**Step 4: Verify revoked access**

Remove a test membership after token issuance. Confirm the relevant request is denied and the UI returns to refreshed trip selection or no-trip state.

**Step 5: Record final evidence**

Add the commands and acceptance outcomes to the implementation handoff or pull request description. Do not add production credentials or OTP values to the repository.

### Task 10: Suppress the selector for a single eligible trip

**Files:**
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/routers/auth.py`
- Modify: `backend/tests/services/test_auth_service.py`
- Modify: `backend/tests/routers/test_auth_trip_selection.py`
- Modify: `frontend/src/features/auth/services/auth-api.ts`
- Modify: `frontend/src/app/providers/auth-context.ts`
- Modify: `frontend/src/app/providers/AuthProvider.tsx`
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`
- Modify: `frontend/src/features/staff/pages/StaffScreen.tsx`
- Modify: relevant frontend tests

Return `can_switch_trips` with every scoped session response, persist it in auth state, hide the switch action when false, and guard the action itself. During membership recovery, automatically select the sole remaining trip; render the selector only for two or more trips. Cover single-trip login, direct switch attempts, traveler/staff controls, and one-trip recovery with failing tests before implementation.

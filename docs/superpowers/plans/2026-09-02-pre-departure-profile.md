# Pre Departure Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a non-duplicative Pre Departure Information section to My Profile and persist its data through the existing profile API.

**Architecture:** Add columns to `traveler_profiles`, expose them through `ProfileUpdate` and `PROFILE_FIELD_DEFAULTS`, save them in `update_profile`, and render them in `ProfileScreen`. The existing `PUT /profile/{user_id}` remains the save endpoint.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, PostgreSQL, React, TypeScript, Vitest, React Testing Library, MSW.

**Spec:** `docs/plans/2026-09-02-pre-departure-profile-design.md`

## Global Constraints

- Do not duplicate fields owned by Registration Details: email, passport, dietary, seasickness, gender, and date of birth.
- Reuse the existing profile API rather than creating a second profile endpoint.
- Persist pre-departure data on `traveler_profiles`.
- Validate date fields with the existing `YYYY-MM-DD` behavior.

---

### Task 1: Backend Persistence

**Files:**
- Modify: `backend/app/db/models/traveler.py`
- Modify: `backend/app/schemas/profile.py`
- Modify: `backend/app/services/profile_service.py`
- Create: `backend/alembic/versions/20260902_0025_add_pre_departure_profile_fields.py`
- Test: `backend/tests/services/test_profile_service.py`
- Test: `backend/tests/integration/test_profile_routes.py`

**Interfaces:**
- Consumes: `update_profile(user_id: str, trip_id: str | None, update: dict, session: AsyncSession) -> dict`
- Produces: new `ProfileData` keys returned in `profile` and listed in `updated_fields`

- [ ] **Step 1: Write failing service and route tests**

Add tests that update and read back `visa_status`, `arrival_date`, `arrival_time`, `arrival_flight`, `departure_date`, `departure_time`, `departure_flight`, `checked_bags`, `travel_insurance_status`, `travel_insurance_brazil_medical_coverage`, `travel_insurance_provider`, `travel_insurance_policy_number`, `travel_insurance_notes`, `roommate_status`, `roommate_email`, `room_configuration`, `roommate_gender_preference`, `extended_stay_help`, `extended_stay_help_details`, `early_check_in_preference`, `emergency_contact`, `instagram_handle`, `trip_mood`, `social_topic`, `always_up_for`, `home_address`, and `final_considerations`.

- [ ] **Step 2: Run backend tests to verify RED**

Run: `cd backend && poetry run pytest tests/services/test_profile_service.py tests/integration/test_profile_routes.py -q`

Expected: FAIL because pre-departure fields are ignored or missing from the database model.

- [ ] **Step 3: Implement backend fields**

Add nullable text/date columns, include them in `ProfileUpdate`, add them to `PROFILE_FIELD_DEFAULTS` and `SUPPORTED_UPDATE_FIELDS`, encode them in `get_profile`, parse date values for arrival/departure dates, and assign all supported fields in `update_profile`.

- [ ] **Step 4: Run backend tests to verify GREEN**

Run: `cd backend && poetry run pytest tests/services/test_profile_service.py tests/integration/test_profile_routes.py -q`

Expected: PASS.

### Task 2: Frontend Profile Section

**Files:**
- Modify: `frontend/src/features/profile/services/profile-api.ts`
- Modify: `frontend/src/features/profile/pages/ProfileScreen.tsx`
- Test: `frontend/src/features/profile/ProfileScreen.test.tsx`

**Interfaces:**
- Consumes: backend profile keys from Task 1
- Produces: one **Pre Departure Information** section that saves through `updateProfile(userId, data)`

- [ ] **Step 1: Write failing frontend test**

Assert that **Pre Departure Information** renders separately from **Registration Details**, does not duplicate passport/dietary controls inside it, and saves a representative payload including visa, arrival/departure, insurance, and emergency contact fields.

- [ ] **Step 2: Run frontend test to verify RED**

Run: `cd frontend && npm test -- ProfileScreen.test.tsx --runInBand`

Expected: FAIL because the section does not exist.

- [ ] **Step 3: Implement frontend section**

Extend `ProfileData`, initialize the form keys, add the new collapsible section after Registration Details, and reuse `handleSave`.

- [ ] **Step 4: Run frontend tests to verify GREEN**

Run: `cd frontend && npm test -- ProfileScreen.test.tsx --runInBand`

Expected: PASS.

### Task 3: Final Verification

**Files:**
- Review all modified files

- [ ] **Step 1: Run focused backend tests**

Run: `cd backend && poetry run pytest tests/services/test_profile_service.py tests/integration/test_profile_routes.py -q`

- [ ] **Step 2: Run focused frontend tests**

Run: `cd frontend && npm test -- ProfileScreen.test.tsx --runInBand`

- [ ] **Step 3: Check git diff**

Run: `git diff --stat` and `git diff --check`


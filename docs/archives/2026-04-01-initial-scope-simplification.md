# Initial Scope Simplification Archive

**Date:** 2026-04-01

## Summary

This archive records the first intentional scope reduction of the traveler app. The active experience was reduced to `Map` and `My Profile` so the product can be rebuilt incrementally on top of a future database-backed architecture.

## Active Experience After Simplification

- Footer navigation: `Map`, `My Profile`
- Top bar: centered title plus notifications button
- Profile sections kept: `Registration Details`, `Products & Payment`, `Service Agreement`

## Removed Frontend Areas

### Navigation and standalone sections

- `Secret Missions`
- `Sharing XP`
- `Local Recommendations`
- `Emergency Contacts`
- `Documents`
- `Group Chat`

### Previous frontend file locations

- `frontend/src/shared/components/BottomNav.tsx`
- `frontend/src/shared/components/TopBar.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/features/missions/pages/MissionsScreen.tsx`
- `frontend/src/features/missions/services/missions-api.ts`
- `frontend/src/features/missions/MissionsScreen.test.tsx`
- `frontend/src/features/sharing/pages/SharingXPScreen.tsx`
- `frontend/src/features/recommendations/pages/RecommendationsScreen.tsx`
- `frontend/src/features/emergency/pages/EmergencyContacts.tsx`
- `frontend/src/features/documents/pages/DocumentsScreen.tsx`

### Frontend cleanup completed

- The route imports and route entries for the removed sections were deleted from `frontend/src/app/router.tsx`.
- The footer now exposes only `Map` and `My Profile`.
- The side menu implementation was removed from `frontend/src/shared/components/TopBar.tsx`.

## Removed Profile Sections

- `eSIM`
- `Roommate`
- `Flight Information`

### Previous profile file location

- `frontend/src/features/profile/pages/ProfileScreen.tsx`

## Removed Backend Areas

### Missions backend

- Route exposure for missions
- Mission service implementation
- Mission schema definitions

### Previous backend file locations

- `backend/app/main.py`
- `backend/app/routers/missions.py`
- `backend/app/services/mission_service.py`
- `backend/app/schemas/missions.py`
- `backend/tests/services/test_mission_service.py`
- `backend/tests/integration/test_mission_routes.py`

### Backend cleanup completed

- Mission router registration was removed from `backend/app/main.py`.
- Mission tables and seeding were removed from `backend/app/db/database.py`.
- Notification route tests were adjusted to stop referencing the removed `/missions` path.

## Reimplementation Notes

- Rebuild removed areas intentionally instead of restoring them wholesale.
- Reintroduce one feature at a time, with a fresh data model and tests.
- If missions return, decide again whether leaderboard, completion, and points all belong in the first reintroduced version.
- If sharing/documents/recommendations/emergency return, define whether they are static content, CMS-backed content, or database-backed user data before recreating routes.
- If profile sections return, add them back only after the related persistence layer exists.

## Recovery Source

- Detailed historical implementation remains available in git history before this simplification.
- This archive should be updated whenever a removed area is intentionally reintroduced.

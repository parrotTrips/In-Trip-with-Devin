# Removed Features Archive

This directory stores the full source of files removed during the initial scope simplification on `2026-04-01`.

## Source of truth

- Archived from `HEAD` before the removal commit is created.
- Paths below mirror the original repository structure to make restoration or selective reuse easier.

## Archived frontend files

- `frontend/src/features/documents/pages/DocumentsScreen.tsx`
- `frontend/src/features/emergency/pages/EmergencyContacts.tsx`
- `frontend/src/features/missions/pages/MissionsScreen.tsx`
- `frontend/src/features/missions/services/missions-api.ts`
- `frontend/src/features/missions/MissionsScreen.test.tsx`
- `frontend/src/features/recommendations/pages/RecommendationsScreen.tsx`
- `frontend/src/features/sharing/pages/SharingXPScreen.tsx`

## Archived backend files

- `backend/app/routers/missions.py`
- `backend/app/schemas/missions.py`
- `backend/app/services/mission_service.py`
- `backend/tests/services/test_mission_service.py`
- `backend/tests/integration/test_mission_routes.py`

## Archived modified active-file snapshots

- `modified-active-files/frontend/src/shared/components/BottomNav.tsx`
- `modified-active-files/frontend/src/shared/components/TopBar.tsx`
- `modified-active-files/frontend/src/app/router.tsx`
- `modified-active-files/frontend/src/features/profile/pages/ProfileScreen.tsx`
- `modified-active-files/frontend/src/features/profile/services/profile-api.ts`
- `modified-active-files/backend/app/main.py`
- `modified-active-files/backend/app/db/database.py`

## Notes

- These files are archived for reference and selective reuse.
- They are intentionally not part of the active application anymore.
- If you restore any of them later, prefer rebuilding around the current data model instead of reattaching the whole archived feature blindly.

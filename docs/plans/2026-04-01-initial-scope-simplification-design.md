# Initial Scope Simplification Design

**Context**

The current app exposes more surface area than the product needs for the first simplified release. The active traveler flow will be reduced to `Map` and `My Profile`, with the removed areas documented for later reimplementation on top of a future database-backed architecture.

**Approved Scope**

- Keep only `Map` and `My Profile` in the active footer navigation.
- Remove `Secret Missions` and `Sharing XP` from the active app.
- Remove the `TopBar` side menu entirely.
- Keep `TopBar` with only the centered title and notifications button.
- Keep only `Registration Details`, `Products & Payment`, and `Service Agreement` inside `My Profile`.
- Remove `Local Recommendations`, `Emergency Contacts`, `Documents`, and `Group Chat` from the active app.
- Remove backend mission exposure from the active backend.

**Archival Strategy**

- Remove the unused feature files from the active frontend and backend.
- Create one archive document describing the removed features, their prior file locations, and the reimplementation notes needed to restore them later.
- Do not preserve removed code in the active source tree; the archive document and git history become the recovery path.

**Frontend Design**

- `BottomNav` becomes a two-item footer with `Map` and `My Profile`.
- `TopBar` no longer renders menu state or the hamburger button.
- `AppRouter` removes inactive routes and imports.
- `ProfileScreen` keeps the existing loading/saving behavior but removes the `eSIM`, `Roommate`, and `Flight Information` sections and the related data fetching that is no longer needed.
- Tests are updated to describe the reduced navigation and profile scope.

**Backend Design**

- Stop including the missions router in `backend/app/main.py`.
- Remove missions router, schema, and service modules from the active backend source tree.
- Preserve the shape of what was removed in the archive document so a future database-backed implementation can be rebuilt intentionally rather than restored blindly.

**Testing**

- Update frontend tests so they assert the reduced footer and simplified profile screen.
- Add or adjust tests to ensure removed labels are absent from active UI composition.
- Run focused frontend tests for app composition, top bar, and profile behavior.

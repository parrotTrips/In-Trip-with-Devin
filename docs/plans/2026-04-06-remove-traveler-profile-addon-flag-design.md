# Remove Traveler Profile Addon Flag Design

**Context**

The current `traveler_profiles` model still includes `receive_addon_updates_flag`. In the current product scope, add-on update consent does not have a clear active use and does not need to stay in the traveler profile schema.

**Goal**

Simplify `traveler_profiles` by removing `receive_addon_updates_flag` from the active database modeling artifacts.

**Approved Scope**

- Remove `receive_addon_updates_flag` from `traveler_profiles`
- Update the active DBML and model docs so they stay aligned
- Leave all other traveler profile fields unchanged

**Modeling Decisions**

- `traveler_profiles` remains the trip-scoped profile table
- Add-on communication consent is not part of the current v1 schema
- No replacement field or table is introduced in this change

**Out of Scope**

- Redesigning traveler marketing consent handling
- Moving consent to another table
- Changing any other traveler profile field

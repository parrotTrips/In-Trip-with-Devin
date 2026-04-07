# Remove Comments and Notifications Design

**Context**

The active product still includes phase/day comments and a notifications feature across the database model, backend APIs, frontend UI, mock data, and tests. The current product scope should exclude both capabilities entirely.

**Goal**

Remove comments and notifications end-to-end so the active schema, backend, frontend, and tests all reflect the reduced product scope.

**Approved Scope**

- Remove `phase_comments` and `notifications` from the active database model
- Remove the related backend tables, routers, schemas, and services
- Remove frontend comments UI, notifications UI, and related API clients
- Remove mock data fields that only exist to support comments
- Remove or update tests that currently exercise these features
- Update DBML, dbdiagram, and modeling docs so the visual and textual model stay aligned

**Modeling Decisions**

- Phases do not support comments in the current scope
- The app does not expose notifications in the current scope
- `trip_phases`, `trip_activities`, checklist progress, and group album remain intact
- Product scope after this change is centered on instructions, checklist, itinerary, album, and profile/product data

**Out of Scope**

- Removing `activity_media`
- Removing phase or traveler progress tracking
- Redesigning the remaining screens beyond stripping the removed features

# Remove Trip Slugs and Timezone Design

**Context**

The current database modeling docs still keep textual `slug` identifiers on trips and trip phases, plus a `default_timezone` on trips. The current product scope does not need URL slugs, slug-based lookup, or configurable per-trip timezone behavior.

**Goal**

Simplify the trip catalog model by removing fields that do not have a clear v1 use in the traveler product.

**Approved Scope**

- Remove `trips.slug`
- Remove `trips.default_timezone`
- Remove `trip_phases.slug`
- Remove the uniqueness rule `UNIQUE (trip_id, slug)` from trip phases
- Update DBML and supporting modeling docs so they stay aligned

**Modeling Decisions**

- `trips` will be identified only by `id` in the current schema
- `trip_phases` will no longer have a textual phase identifier
- The ERD planning docs should no longer describe `(trip_id, slug)` as a preserved uniqueness rule

**Out of Scope**

- Adding replacement URL identifiers
- Introducing timezone handling at another layer
- Changing unrelated traveler, activity, checklist, or media structures

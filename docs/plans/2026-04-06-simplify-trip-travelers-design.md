# Simplify Trip Travelers Design

**Context**

The current `trip_travelers` model still stores `display_name`, `enrollment_status`, and `joined_at`. In the current traveler-only product scope, those attributes do not have a clear purpose, but the association entity itself is still important because many traveler-in-trip tables point to it.

**Goal**

Simplify `trip_travelers` by removing fields that do not have a clear v1 use, while keeping `id` as the stable identifier for the traveler-trip association.

**Approved Scope**

- Remove `display_name` from `trip_travelers`
- Remove `enrollment_status` from `trip_travelers`
- Remove `joined_at` from `trip_travelers`
- Remove related documentation statements and checks tied to those fields
- Keep `id`, `trip_id`, `user_id`, timestamps, and `UNIQUE (trip_id, user_id)`

**Modeling Decisions**

- `trip_travelers` continues to represent the traveler inside a specific trip
- `trip_travelers.id` remains the single identifier referenced by traveler-specific child tables
- Existence of the row itself now represents participation in the trip
- The uniqueness rule on `trip_id + user_id` still prevents duplicate participation rows

**Out of Scope**

- Replacing `trip_travelers.id` with a composite primary key
- Refactoring child tables away from `trip_traveler_id`
- Changing traveler profile, product, or progress structures beyond preserving their existing foreign key

# Simplify Trip Activities Design

**Context**

The current `trip_activities` model still includes `activity_code`, `price_label`, and `vibe`. The chosen product direction is simpler: activities do not need a separate code, price should be stored as a numeric value in BRL when present, and `vibe` is not part of the current schema.

**Goal**

Simplify `trip_activities` by removing nonessential descriptive/code fields and replacing the free-form price label with a structured BRL amount.

**Approved Scope**

- Remove `activity_code` from `trip_activities`
- Remove `price_label` from `trip_activities`
- Add `amount_brl` to `trip_activities`
- Remove `vibe` from `trip_activities`
- Remove the uniqueness rule `UNIQUE (trip_phase_id, activity_code)`
- Update active DBML and modeling docs to stay aligned
- Remove `vibe` from the active frontend mock data shape because it is not used by the UI

**Modeling Decisions**

- Activities are identified by `id` in the current schema
- When an activity has a price, it is stored as `amount_brl numeric(12,2)`
- No replacement textual code is introduced
- No replacement field for `vibe` is introduced

**Out of Scope**

- Refactoring frontend `price` rendering to consume `amount_brl`
- Adding multi-currency support
- Changing activity media or phase relationships

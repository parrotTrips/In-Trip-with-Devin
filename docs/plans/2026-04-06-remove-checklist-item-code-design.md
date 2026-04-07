# Remove Checklist Item Code Design

**Context**

The current `trip_phase_checklist_items` model still includes `item_code` plus a uniqueness rule on `(trip_phase_id, item_code)`. The current product scope does not require a separate textual identifier for checklist items.

**Goal**

Simplify checklist items so they are identified only by `id`, without a separate code field.

**Approved Scope**

- Remove `item_code` from `trip_phase_checklist_items`
- Remove the uniqueness rule `UNIQUE (trip_phase_id, item_code)`
- Update the active DBML and modeling docs to stay aligned
- Update prior planning docs that still describe `item_code` as intentionally preserved

**Modeling Decisions**

- Checklist items are identified by `id` in the current schema
- `label` remains presentation text and is not forced into a uniqueness role
- No replacement code field is introduced

**Out of Scope**

- Adding a new checklist identity scheme
- Changing traveler progress tables
- Redesigning checklist behavior beyond this schema simplification

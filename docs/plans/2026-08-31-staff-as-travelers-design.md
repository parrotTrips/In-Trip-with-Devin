# Staff as Travelers Design

## Context

Staff users need to operate the staff workflow and also open the traveler-facing app for the same trip. The traveler app resolves active trip, phases, QR code, announcements, team, contacts, recommendations, FAQ, and feedback through `trip_travelers`.

## Decision

The Staff sheet import remains the source of truth for operational staff. For every row in the `Staff` tab, the import must:

1. create or update the `users` row with `role = 'staff'`;
2. ensure a matching `trip_travelers` row exists for the same `wetravel_trip_uuid` and user;
3. create or update the `trip_staff` row with function, photo, and bio.

This keeps the model explicit: `trip_staff` controls staff capabilities and display metadata, while `trip_travelers` grants traveler app access and QR/progress identity.

## Rejected Alternatives

- A one-off insert for Gabriel fixes only the current symptom and does not protect future imports.
- Adding `trip_staff` fallback logic to all traveler routes spreads access rules across the app and still leaves missing traveler IDs for QR/check-in/progress features.

## Validation

Add regression coverage to `write_staff` proving the import creates the traveler link. Then run the Staff import/backfill for `TEST-2026-FULL` in production and verify Gabriel has both `trip_staff` and `trip_travelers` links.

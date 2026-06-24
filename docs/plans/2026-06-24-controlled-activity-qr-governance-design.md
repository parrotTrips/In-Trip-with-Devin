# Controlled Activity QR Governance Design

## Goal

Prevent travelers from being checked into optional or controlled activities they are not authorized to join, while keeping normal activity check-ins operationally simple.

## Product Rule

An activity is controlled only when it has at least one row in the Staff spreadsheet tab `Participantes Atividades`. Activities without rows in that tab keep the current behavior: any traveler linked to the trip can be checked in.

The tab format is:

```text
trip_uuid | dia | atividade_nome | traveler_phone | status
```

`status = allowed` means the traveler can be checked into that activity. Other statuses are ignored by the first version.

## Data Model

Add `activity_participants`:

- `id`
- `trip_activity_id`
- `trip_traveler_id`
- `status`
- `created_at`
- `updated_at`

Use a unique constraint on `(trip_activity_id, trip_traveler_id)`.

Add `activity_checkin_scan_events`:

- `id`
- `trip_activity_id`, nullable because invalid QR may not resolve to an activity validation context
- `trip_traveler_id`, nullable because invalid QR may not identify a traveler
- `scanned_by_user_id`
- `status`
- `failure_reason`
- `raw_payload_hash`
- `created_at`

This table records every scan attempt that reaches the backend, including rejected and duplicate attempts.

## Backend Flow

The staff scan endpoint keeps activity-scoped scanning. After QR decoding and trip membership validation, it checks whether the activity is controlled:

1. Count rows in `activity_participants` for the activity.
2. If zero rows, continue with current check-in behavior.
3. If one or more rows exist, require the scanned traveler to have an `allowed` row for that activity.
4. If missing, return `403` with a clear message and record an audit event.

Every terminal outcome records an audit event:

- `checked_in`
- `already_checked_in`
- `invalid_qr`
- `activity_not_found`
- `activity_outside_staff_trip`
- `traveler_not_found`
- `traveler_outside_staff_trip`
- `not_traveler`
- `not_authorized_for_activity`

## Import Flow

Add a parser and writer to `backend/scripts/import_staff_content.py` for the `Participantes Atividades` tab. The writer resolves:

- `dia` to in-trip day number;
- `atividade_nome` to `trip_activities.name`;
- `traveler_phone` to a `users` row with `role = traveler`;
- traveler membership through `trip_travelers`.

The import deletes current `activity_participants` for the trip and recreates them from the sheet.

Add admin endpoint:

```text
POST /admin/trips/import-activity-participants
```

## Staff App

The first version only needs better error feedback from the backend. If a traveler is not allowed for a controlled activity, the existing scanner error area shows:

```text
Traveler is not authorized for this activity.
```

No new screen is required for this version.

## Audit Use

Operations can audit the database by joining `activity_checkin_scan_events` with:

- `trip_activities`
- `trip_phases`
- `users` for staff
- `trip_travelers` and `users` for traveler identity

Later, this can become an admin export or a Staff app audit view.


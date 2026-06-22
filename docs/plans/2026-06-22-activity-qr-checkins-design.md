# Activity QR Check-ins Design

## Goal

Allow travelers to present one personal QR code and allow staff to check travelers into one specific trip activity by scanning that QR from inside the activity context.

## Product Rules

- The traveler QR identifies the traveler for the active trip.
- The staff app determines the activity context. The QR itself does not choose the activity.
- A traveler can be checked in only once per activity.
- A duplicate scan must not create another check-in. It should tell staff who already scanned the traveler and when.
- Each staff activity should show a check-in counter, for example `12 / 38 travelers checked in`.
- The denominator is the count of travelers linked to the trip, excluding users whose role is `staff`.
- The numerator is the count of unique traveler check-ins for that activity.

## Recommended UX

### Traveler

Add a `My QR Code` area in the traveler app. The QR payload should identify the traveler-trip membership, preferably by `trip_traveler_id` plus a signed token so a fake QR cannot be hand-written easily.

### Staff

Remove the current global meaning of the `QR Scan` tab as the primary scan flow. Staff should scan from inside an activity:

1. Open Staff itinerary.
2. Open Day.
3. Open Activity.
4. Tap `Scan Travelers`.
5. Scan traveler QR.
6. See one of:
   - success: traveler checked in;
   - duplicate: already checked in by staff member at timestamp;
   - invalid: QR is not valid for this trip;
   - wrong trip/member: traveler does not belong to this trip.

The global `QR Scan` tab can remain as a helper screen, but it should require selecting an activity before scanning. The safer first version is to make scanning activity-first and not rely on the global tab.

## Data Model

Create a new `activity_checkins` table:

- `id`
- `trip_activity_id`
- `trip_traveler_id`
- `scanned_by_user_id`
- `checked_in_at`
- `created_at`
- `updated_at`

Constraints:

- foreign key `trip_activity_id -> trip_activities.id`
- foreign key `trip_traveler_id -> trip_travelers.id`
- foreign key `scanned_by_user_id -> users.id`
- unique constraint on `(trip_activity_id, trip_traveler_id)`

This enforces one check-in per traveler per activity at the database level.

## API

Traveler:

- `GET /me/qr-code`
  - Returns the active trip traveler ID and a signed QR payload.

Staff:

- `POST /me/staff/activities/{activity_id}/checkins/scan`
  - Body: scanned QR payload.
  - Uses the authenticated staff user as `scanned_by_user_id`.
  - Validates the QR signature.
  - Validates that traveler and activity belong to the same active trip.
  - Creates the check-in if missing.
  - Returns duplicate metadata if it already exists.

- `GET /me/staff/trip`
  - Include per activity:
    - `checkin_count`
    - `traveler_count`

Optionally include recent/checked-in traveler details later. The first version only needs counts and scan responses.

## Security

The QR payload should not be just a raw user ID. Use a signed payload with:

- `trip_traveler_id`
- `trip_uuid`
- `type: traveler_checkin`
- signature using `JWT_SECRET` or a dedicated QR signing secret

The backend must validate the signature and must not trust client-provided activity IDs beyond the URL path and authenticated staff context.

## Testing

Backend tests should cover:

- first scan creates a check-in;
- duplicate scan returns duplicate status and does not create a second row;
- wrong trip QR is rejected;
- scan by staff stores `scanned_by_user_id`;
- staff trip endpoint includes `checkin_count` and `traveler_count`.

Frontend tests should cover:

- traveler QR tab renders QR payload;
- staff activity shows the counter;
- staff opens scanner from a specific activity;
- duplicate scan shows duplicate state.


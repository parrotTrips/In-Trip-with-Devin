# Staff Camera QR Scanner Design

## Goal

Let staff scan traveler QR codes from the activity they are operating, so each scan is validated against the intended activity.

## Current State

The backend already supports activity-scoped scans through `POST /me/staff/activities/{activity_id}/checkins/scan`. The staff app currently exposes scanning through an activity panel, but the scanner is a manual QR payload textarea. The app also still has a global `QR Scan` tab, which does not map naturally to a specific activity.

The existing activity counter uses `checkin_count / traveler_count`. For now, `traveler_count` remains the total traveler count for the trip, not an activity-specific participant count.

## Approach

Use camera scanning inside the expanded activity panel. When staff taps `Scan Travelers`, the UI opens a scanner tied to that activity. A successful QR decode sends the decoded payload to the existing activity scan endpoint with that activity's ID.

The scanner pauses while a scan request is in flight to avoid repeated submissions from the same QR code. After the backend responds, the UI shows success, duplicate, or error feedback and allows scanning to continue.

## UI Changes

- Remove the global staff `QR Scan` tab.
- Keep the activity itinerary and contacts tabs.
- Keep `Scan Travelers` inside each expanded activity.
- Replace the manual-first scanner with a camera-first panel.
- Keep a small manual fallback for cases where camera permission or browser camera support fails.
- Keep the current counter behavior: `checkin_count / traveler_count`, where `traveler_count` is the total traveler count for the trip.

## Data Flow

1. Staff opens a day.
2. Staff expands an activity.
3. Staff taps `Scan Travelers`.
4. The camera scanner decodes a traveler QR payload.
5. The frontend calls `scanActivityTraveler(activity.id, decodedPayload)`.
6. The backend validates the QR payload and activity.
7. The frontend updates only that activity's local `checkin_count` when the response status is `checked_in`.

## Error Handling

- Invalid QR payload: show the backend error message.
- Duplicate scan: show who originally scanned it and when, when available.
- Camera permission denied or unavailable: show a clear error and offer manual entry.
- Repeated reads of the same QR while submitting: ignored until the request finishes.

## Testing

Frontend tests should mock the camera scanner because `jsdom` does not provide a real camera. Coverage should verify:

- The global `QR Scan` tab is gone.
- The activity counter still renders with total trip travelers.
- Opening `Scan Travelers` starts an activity-scoped camera panel.
- A decoded QR payload posts to the activity scan endpoint.
- A successful scan increments the local activity count.
- Duplicate scans do not increment the local count.
- Manual fallback can still submit a payload.

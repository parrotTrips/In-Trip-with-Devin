# Feedback Submissions Sheet Sync Design

## Goal

Change app feedback from one editable value per traveler/trip into append-only submissions stored in Supabase, with an operational Google Sheets sync that imports feedbacks on demand.

## Current State

Feedback currently uses `traveler_app_feedback` with a unique constraint on `trip_traveler_id`. The traveler app loads the existing feedback through `GET /me/app-feedback`, lets the traveler edit it, and writes through `PUT /me/app-feedback`. The Google Sheets admin menu does not expose feedback.

## Chosen Approach

Supabase remains the source of truth. Each traveler submission creates a new row in `traveler_app_feedback`. The Google Sheet is updated manually from the spreadsheet menu by calling an admin endpoint that reads Supabase and rewrites a `Feedbacks` tab for the selected trip.

This avoids making the traveler-facing send action depend on Google Sheets availability. It also gives operations a simple spreadsheet view without introducing a second write path.

## Data Model

Keep the existing `traveler_app_feedback` table, but remove the unique constraint on `trip_traveler_id`. Each row represents one submission.

Fields used by the workflow:

- `id`
- `trip_traveler_id`
- `feedback`
- `created_at`
- `updated_at`

The sync joins through `trip_travelers` and `users` so the sheet can show trip, traveler name, and phone.

## API

Traveler:

- `POST /me/app-feedback`
- Body: `{ "feedback": "..." }`
- Behavior: trim text, create a new feedback row, return `feedback`, `id`, and `created_at`.

The frontend no longer needs to call `GET /me/app-feedback` for the feedback textarea.

Admin:

- `POST /admin/trips/sync-feedback-to-sheet`
- Body: `{ "trip_uuid": "..." }`
- Behavior: read all feedback rows for the trip from Supabase, create or clear the `Feedbacks` tab in the trip content spreadsheet, write headers and rows, return counts.

## Sheet

Add a `Feedbacks` tab with these columns:

- `feedback_id`
- `trip_uuid`
- `traveler_name`
- `phone`
- `feedback`
- `created_at`

Add an Apps Script menu item:

- `💬 Import Feedbacks from App`

The menu prompts for a trip and calls the admin endpoint.

## Frontend UX

The Information feedback section becomes a send-only form:

- No saved feedback is loaded into the textarea.
- On send, the frontend calls `POST /me/app-feedback`.
- On success, it shows `Feedback sent`, clears the textarea, and emits `app_feedback_sent` to PostHog.
- On failure, it keeps the typed text and shows the existing error message.

## Testing

- Backend integration test: two submissions by the same traveler in the same trip create two database rows.
- Backend/admin unit or integration test: sync writes feedback rows for the selected trip to the sheet writer path.
- Frontend test: feedback textarea starts empty, sends with `POST`, shows success, and clears.
- Apps Script label test: the feedback import menu item exists.

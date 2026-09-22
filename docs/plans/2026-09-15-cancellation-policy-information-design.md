# Cancellation Policy in Information Design

## Goal

Show the trip cancellation policy in the traveler app so operators can see how rows from the `Cancellation Policy` sheet appear to travelers.

## Chosen Approach

Add a collapsible `Cancellation Policy` section to the existing `Information` screen, placed below `FAQ`. The screen will call the existing `GET /me/cancellation-policy` endpoint through the already defined `getMyCancellationPolicy()` client and render each item as a title/body block ordered by the backend response.

## Data Flow

The Google Sheet tab `Cancellation Policy` exports rows into `trip_cancellation_policies`. The traveler app loads those rows through `/me/cancellation-policy`; each row appears as one policy block using `title` and `body`.

## Empty and Error Behavior

If no rows exist, the section shows `No cancellation policy yet`. The screen already treats loading failures as non-blocking, so this endpoint should follow the same pattern as team, emergency contacts, and FAQ.

## Testing

Update `InformationScreen.test.tsx` to assert that the screen loads `/me/cancellation-policy`, shows the `Cancellation Policy` section, and renders the policy title and body when expanded.

# Pre Departure Profile Design

## Goal

Add a new **Pre Departure Information** section to **My Profile** so travelers can submit pre-trip logistics from the Parrot Trips pre-departure form without duplicating fields already collected in **Registration Details**.

## Source Of Truth

Registration Details remains the canonical place for personal identity, email, passport, date of birth, gender, dietary restrictions, and seasickness information.

Pre Departure Information only owns logistics and preference data that is not already represented elsewhere:

- Visa status
- Arrival date, arrival time, and arrival airport/flight
- Departure date, departure time, and departure airport/flight
- Checked bags
- Travel insurance status, Brazil medical coverage, provider, policy number, and notes
- Roommate knowledge, requested roommate email, room configuration, and gender preference for matching
- Early or extended stay help and first-hotel early check-in preference
- Emergency contact
- Instagram handle
- Trip mood, social topic, always-up-for preferences
- Home address
- Final considerations

## Architecture

Persist the new fields on `traveler_profiles`, next to existing profile data, because the data belongs to one traveler within one trip. The existing `GET /profile/{user_id}` and `PUT /profile/{user_id}` flow continues to be the only profile API surface. The frontend extends `ProfileData`, loads the values with the existing profile response, and saves through the existing `updateProfile` request.

## UI

`ProfileScreen` gets one additional collapsible section titled **Pre Departure Information**. It should sit after **Registration Details** and before **Packages**, so the profile flows from identity to pre-trip logistics to read-only purchase documents.

The section must not ask for email, passport, dietary, seasickness, gender, or date of birth. It may include a final free-text field for changes or details the traveler wants Parrot Trips to know.

## Validation

The backend should parse pre-departure dates as `YYYY-MM-DD` and reject invalid values with the same 422 pattern used by existing profile dates. Select/radio values are stored as strings matching the current public form labels. Checkbox groups are stored as a text value containing selected labels joined by newlines from the frontend.


# Pre-Departure Date, Time, and Help UX Design

## Goal

Improve the traveler-facing Pre Departure form by replacing manually formatted
arrival and departure date/time fields with constrained controls and by reducing
the visual weight of explanatory copy.

## Interaction design

- Arrival Date and Departure Date use the browser's native calendar control.
  The application continues to store and submit dates as `YYYY-MM-DD`.
- Arrival Time and Departure Time use select controls containing every five-minute
  interval from `12:00 AM` through `11:55 PM`. Values continue to be submitted as
  24-hour `HH:mm` strings.
- Existing saved values remain selectable. A legacy time that is not on a
  five-minute boundary is retained as an additional option so opening and saving
  the form does not silently alter stored data.
- Each explanatory message is placed immediately after its related field:
  - check-in guidance after Early Check-in Preference;
  - Instagram guidance after Instagram Handle;
  - hotel address guidance after Home Address.
- Guidance is collapsed by default. A small `More information` button toggles the
  corresponding text and exposes its expanded state to assistive technology.

## Scope

This is a frontend-only change in the traveler profile screen. API payloads,
backend validation, database columns, and migrations remain unchanged.

## Accessibility and responsive behavior

Native date and select controls retain explicit labels and validation metadata.
Help toggles are real buttons with `aria-expanded` and `aria-controls`. Existing
one-column mobile and two-column larger-screen layouts remain unchanged.

## Testing

Profile screen tests will verify native date controls, five-minute time choices,
payload compatibility, default-collapsed help, help expansion, and placement of
each help control after its associated field.

# Journey Sticky Current Phase Design

## Goal

Freeze the Journey summary header while the traveler scrolls the phase path, and open the Journey centered on the traveler's current phase.

## Design

Keep the existing white `AppHeader` fixed at the top of the viewport. Convert the green Journey summary block in `frontend/src/features/trip/pages/HomeScreen.tsx` into a sticky header positioned directly below it with `top: 56px`.

The sticky block keeps the same content: trip title, staff-view switch, trip dates, trip mode, and progress bar. The phase path remains the scrollable content underneath.

After trip data loads, the screen will locate the phase card whose id matches the current traveler's `current_phase_id`. If found, it will scroll that card into the center of the visible area. If no current phase exists or the phase is not rendered, the screen keeps the normal top position.

## Testing

Add focused tests in `frontend/src/features/trip/HomeScreen.test.tsx` to verify:

- the Journey summary is exposed as a sticky region;
- the current phase element is targeted for automatic centering after load.

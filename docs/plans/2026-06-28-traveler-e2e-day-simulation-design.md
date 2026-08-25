# Traveler E2E Test And Day Simulation Design

## Goal

Create a beginner-friendly traveler E2E test guide and keep day simulation as an internal backend script, not as a production app control.

## Recommended Approach

Use the existing `backend/scripts/simulate_trip_day.py` as the operational tool for simulating in-trip days. Improve it so reset can work for newly created WeTravel test trips by reading `wetravel_trips.start_date` instead of using hardcoded dates from the old test trip.

Create `docs/testing/traveler_e2e_test_plan.md` as the human-readable test guide. The guide will start at WeTravel, move through spreadsheet/import steps, and end inside the deployed traveler app. Each step will include what to do, what to check, and what to write down if something fails.

## Alternatives Considered

1. Add a hidden button in the app to simulate days.
   - Easier for testers.
   - Riskier because a production UI could mutate live trip timing.

2. Add an admin endpoint to simulate days.
   - Useful later for automated QA.
   - Still exposes a production mutation path that is not needed yet.

3. Keep simulation as a backend script.
   - Safer for now.
   - Fits the current operational workflow.
   - Requires someone technical to run the command, but avoids exposing test controls to users.

## Chosen Design

Use option 3.

The script will continue to update `trip_phases.starts_at` for `phase_type = 'in-trip'`. The traveler app already uses those dates to decide which in-trip days have started. For reset, the script should reconstruct dates from `wetravel_trips.start_date` plus each in-trip day order.

## Testing

Add unit tests around pure date helper functions in `backend/scripts/simulate_trip_day.py`. These tests should verify:

- simulated past/future dates around a target day;
- reset dates generated from a trip start date;
- invalid simulation day values are rejected.


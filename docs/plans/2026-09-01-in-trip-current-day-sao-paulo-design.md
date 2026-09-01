# In-Trip Current Day Sao Paulo Design

## Goal

When a trip switches from pre-trip to in-trip, all travelers should appear on the current in-trip day, regardless of unfinished pre-trip phases.

## Design

Keep `current_phase_id` as the single field consumed by the frontend. Change the backend logic that computes this field in `get_trip_travelers`.

If `trip_settings.mode` is `pre-trip`, keep the current behavior: each traveler remains on their first incomplete pre-trip phase based on `traveler_phase_progress`.

If `trip_settings.mode` is `in-trip`, ignore pre-trip completion state and compute the active in-trip phase from calendar dates. Date comparison must use `America/Sao_Paulo`, so the app changes from Day 1 to Day 2 at `00:00` Sao Paulo time.

Boundary behavior:

- before the first in-trip day, return the first in-trip phase;
- during a day, return the latest in-trip phase whose local Sao Paulo date is today or earlier;
- after the last in-trip day starts, return the last in-trip phase;
- if no in-trip phases exist, fall back to the existing ordered phase logic.

## Testing

Add unit tests for:

- `23:59` Sao Paulo on Day 1 still returns Day 1;
- `00:00` Sao Paulo on Day 2 returns Day 2;
- pre-trip mode continues to respect incomplete pre-trip phases.

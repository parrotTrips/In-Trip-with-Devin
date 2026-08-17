# Casamento GaRapha Seed Design

## Goal

Create the minimal production data needed for the wedding trip `CASAMENTO-GARAPHA-2026` to appear in the app with Gabriela and Raphael as travelers.

## Scope

- Create or update the base trip in `wetravel_trips`.
- Create or update `trip_settings` in `pre-trip` mode.
- Create or update two `users` with role `traveler`.
- Link both users to the trip through `trip_travelers`.
- Create or update basic `traveler_profiles`.
- Create or update basic `traveler_products` where that table exists.
- Update Google Sheets audit/reference tabs for the trip and travelers.

## Deferred

- Do not import the full wedding itinerary yet.
- Do not create check-in allowlists, staff tasks, QR PNGs, or announcements yet.
- Do not overwrite unrelated trips or unrelated rows in the shared spreadsheets.

## Data

- `trip_uuid`: `CASAMENTO-GARAPHA-2026`
- title: `Casamento Gabriela e Raphael`
- destination: `Prea, Ceara, Brasil`
- dates: `2026-09-04` to `2026-09-06`
- URL: `https://sites.icasei.com.br/gabrielaeraphael/home`
- travelers:
  - Gabriela, `+5534991825752`
  - Raphael, `+5511993741189`

## Approach

Use a dedicated idempotent script rather than editing existing test seed constants. The script should default to dry-run, use `--execute` for writes, and support `--skip-sheets` so Supabase and Google Sheets writes can be verified independently.


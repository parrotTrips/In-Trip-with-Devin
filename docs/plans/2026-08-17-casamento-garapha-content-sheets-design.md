# Casamento GaRapha Content Sheets Design

## Goal

Populate the `CASAMENTO-GARAPHA-2026` wedding trip with all filled content from `docs/data-requests/20260806-data-request-casamento-garapha.md`, while keeping Google Sheets as the auditable source before importing into Supabase.

## Source Content

The source document contains:

- General wedding data: title, dates, destination, main venue, welcome message, wedding website.
- Ceremony support contact: Marine Carneiro.
- Programacao geral: four public moments across September 4-6, 2026.
- Activity details: locations, map links, participation, descriptions, practical notes, dress code, transport notes, and QR check-in answers.
- FAQ: dress code, transportation, and ceremony arrival timing.
- Pre-wedding preparation phases: travel logistics, packing, and wellbeing.
- Local recommendations: sports, tourism, beauty, transportation, and restaurants.
- Useful links: wedding website and gift list.

## Approach

Use the existing shared trip-content spreadsheet flow as the source of truth. First write rows for `CASAMENTO-GARAPHA-2026` into the relevant tabs, preserving rows for all other trips. Then run the existing import flow, extending it only where needed for content types that are not currently imported.

This keeps the wedding trip aligned with the same operational model used by the test trip: pre-trip phases remain visible while the trip mode is `pre-trip`, and the three event days are already loaded as `in-trip` phases for later mode switching.

## Spreadsheet Mapping

Write or update only rows where `trip_uuid = CASAMENTO-GARAPHA-2026`.

- `Viagens`: wedding title, start/end dates, and no service agreement URL unless one is provided later.
- `Fases`: pre-trip preparation phases.
- `Checklist`: checklist items for each pre-trip phase.
- `Links`: wedding website, gift list, and key maps.
- `Roteiro`: the three wedding days and their activities.
- `Contatos`: Marine Carneiro as the ceremony/support contact.
- `Recomendacoes`: local recommendations from the document.
- `FAQ`: the filled FAQ rows.

## Pre-Trip Content

Keep `trip_settings.mode = pre-trip`.

Pre-trip phases:

1. `Logistica de Viagem`: confirm flights, lodging, transfer to Prea, and personal documents.
2. `Preparando as Malas`: welcome dinner outfit, beach outfit, wedding outfit, sunscreen, repellent, sandals, sunglasses, and personal medication.
3. `Cuidados e Bem-estar`: hydration, personal hygiene kit, sunglasses check, and climate/beach readiness.
4. `Informacoes do Casamento`: review the wedding website, main venue, ceremony arrival guidance, transport expectations, and gift list.

## In-Trip Content

Create three `in-trip` day phases:

1. `04/09/2026`: welcome dinner at Rancho do Kite.
2. `05/09/2026`: jangada ride and pre-wedding lunch/party.
3. `06/09/2026`: wedding ceremony and party.

Activities should be informational only for now. Do not enable QR check-in restrictions or participant allowlists because the document marks check-in as `Nao` or leaves it blank.

## Other App Content

- FAQ appears in the Information screen.
- Marine Carneiro appears as an emergency/support contact.
- Recommendations appear in Local Recommendations.
- Staff access remains unchanged for Bela and Jaqueline.

## Testing

Use focused backend tests for row-building/parsing helpers before writing to Sheets or Supabase. Then verify with read queries that the spreadsheet import created:

- four pre-trip phases;
- three in-trip days;
- four activities;
- FAQ rows;
- contact row;
- recommendations rows;
- useful links.

Finally, verify the app-facing APIs for Gabriela or Raphael return the expected content while the trip remains in `pre-trip`.

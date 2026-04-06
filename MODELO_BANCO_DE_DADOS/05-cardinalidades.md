# Cardinalidades e Optionalidade

## Identidade e participação

- `User 1 -> 0..N TripTraveler`
- `Trip 1 -> 0..N TripTraveler`
- `TripTraveler N -> 1 User`
- `TripTraveler N -> 1 Trip`

## Perfil e dados operacionais do viajante

- `TripTraveler 1 -> 0..1 TravelerProfile`
- `TripTraveler 1 -> 0..1 TravelerProduct`
- `TravelerProduct 0..N -> 0..1 MediaAsset`

## Catálogo da viagem

- `Trip 1 -> 0..N TripPhase`
- `TripPhase 0..N -> 0..1 TripPhase (parent)`
- `TripPhase 1 -> 0..N TripPhaseChecklistItem`
- `TripPhase 1 -> 0..N TripPhaseLink`
- `TripPhase 1 -> 0..N TripPhaseAttachment`
- `TripPhase 1 -> 0..N TripActivity`
- `TripPhaseAttachment N -> 1 MediaAsset`
- `MediaAsset 1 -> 0..N TripPhaseAttachment`
- `TripActivity 1 -> 0..N ActivityMedia`
- `ActivityMedia N -> 1 MediaAsset`
- `MediaAsset 1 -> 0..N ActivityMedia`

## Progresso e interação

- `TripTraveler 1 -> 0..N TravelerChecklistProgress`
- `TripPhaseChecklistItem 1 -> 0..N TravelerChecklistProgress`
- `TripTraveler 1 -> 0..N TravelerPhaseProgress`
- `TripPhase 1 -> 0..N TravelerPhaseProgress`
- `TripTraveler 1 -> 0..N PhaseComment`
- `TripPhase 1 -> 0..N PhaseComment`
- `TripTraveler 1 -> 0..N Notification`

## Relações 1:1 importantes

Estas relações devem ser modeladas como `1 -> 0..1`:

- `TripTraveler -> TravelerProfile`
- `TripTraveler -> TravelerProduct`

Implementação recomendada:

- `UNIQUE (trip_traveler_id)` nas tabelas filhas

## Relações N:N resolvidas por tabelas associativas

### `users <-> trips`

Resolvida por:

- `trip_travelers`

### `trip_travelers <-> trip_phase_checklist_items`

Resolvida por:

- `traveler_checklist_progress`

### `trip_travelers <-> trip_phases`

Resolvida por:

- `traveler_phase_progress`

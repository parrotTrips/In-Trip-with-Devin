# Traveler-Only Domain Design

**Context**

The current database modeling docs still describe a mixed domain with travelers plus internal backoffice users. The product direction has changed: the app and its modeled data should now represent only travelers.

**Goal**

Simplify the domain so the user model and the supporting database documentation describe only traveler-facing behavior.

**Approved Scope**

- Remove `users.role` from the data model documentation and DBML artifact
- Remove documentation statements that depend on internal users, admin roles, or backoffice participants
- Keep the rest of the trip and traveler participation model intact
- Preserve `trip_travelers` as the central traveler-in-trip entity

**Modeling Decisions**

- `users` now represents authenticated travelers only
- `trip_travelers` remains the participation layer for a traveler inside a specific trip
- No internal `team` or `admin` role is modeled in the current schema
- No backoffice-specific access pattern is part of the current database scope

**Out of Scope**

- Introducing a replacement permission model
- Refactoring unrelated product copy in the frontend
- Changing trip, phase, checklist, or media structures beyond the removal of role/backoffice assumptions

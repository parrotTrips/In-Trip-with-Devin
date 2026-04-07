# Remove Phase Attachments Design

**Context**

The current model includes `trip_phase_attachments` and the active frontend still renders a "Documents" section inside a phase. The current product direction does not need phase-specific attached files as a separate concept; phases should rely on text, checklist, links, itinerary, and album.

**Goal**

Remove the phase attachments concept from the active schema, modeling docs, and active frontend UI/mock data.

**Approved Scope**

- Remove `trip_phase_attachments` from the active database model
- Remove the related relationships and storage references from the active model docs
- Remove `attachments` from the active frontend phase mock shape and screen rendering
- Remove the entity from the DB diagram artifact so the visual model stays aligned

**Modeling Decisions**

- Phases do not have a dedicated attachment/document entity in the current product scope
- If a phase needs external resources, they should be represented through `trip_phase_links`
- `media_assets` remains in the schema for activity media and traveler product service agreements

**Out of Scope**

- Removing `activity_media`
- Removing `media_assets`
- Redesigning instruction content beyond the removal of phase attachments

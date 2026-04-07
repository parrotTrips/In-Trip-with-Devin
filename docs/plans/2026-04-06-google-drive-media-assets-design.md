# Google Drive Media Assets Design

**Context**

The current `media_assets` model is generic and provider-agnostic, with fields such as `storage_provider`, `storage_bucket`, and `storage_key`. The chosen product direction is simpler: media will always be organized in Google Drive using folders and subfolders.

**Goal**

Redesign `media_assets` so it models Google Drive file references directly, without generic storage-provider abstractions.

**Approved Scope**

- Replace generic storage fields with Google Drive-oriented fields
- Remove `file_size_bytes`
- Keep the table lightweight and not overly detailed
- Update the DBML and all active database-modeling docs to match the new approach

**Modeling Decisions**

- `media_assets` stores a stable Google Drive file identifier in `drive_file_id`
- `drive_path` stores the human-readable folder/subfolder path used by the team
- `public_url` remains available as the access/share link
- `mime_type` and `original_filename` remain as simple metadata
- `UNIQUE (drive_file_id)` is enough for identity in this version

**Out of Scope**

- Modeling Drive folders as a separate entity
- Storing detailed permission metadata
- Adding sync/audit fields beyond the current timestamps

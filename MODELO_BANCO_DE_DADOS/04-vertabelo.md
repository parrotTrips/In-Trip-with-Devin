# Modelo para Vertabelo

## Tabelas e colunas-chave

### `users`

- `id uuid PK`
- `phone text NOT NULL UNIQUE`
- `full_name text NULL`
- `email text NULL`
- `status text NOT NULL`
- `role text NOT NULL`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

Checks:

- `status in ('active', 'inactive', 'blocked')`
- `role in ('traveler', 'team', 'admin')`

### `trips`

- `id uuid PK`
- `slug text NOT NULL UNIQUE`
- `name text NOT NULL`
- `short_name text NULL`
- `description text NULL`
- `start_date date NOT NULL`
- `end_date date NOT NULL`
- `status text NOT NULL`
- `default_timezone text NOT NULL`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

Checks:

- `status in ('draft', 'published', 'archived')`

### `trip_travelers`

- `id uuid PK`
- `trip_id uuid NOT NULL FK -> trips.id`
- `user_id uuid NOT NULL FK -> users.id`
- `display_name text NULL`
- `enrollment_status text NOT NULL`
- `joined_at timestamptz NULL`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

Regras:

- `UNIQUE (trip_id, user_id)`

Checks:

- `enrollment_status in ('invited', 'active', 'cancelled')`

### `traveler_profiles`

- `id uuid PK`
- `trip_traveler_id uuid NOT NULL UNIQUE FK -> trip_travelers.id`
- campos cadastrais e documentais
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

### `traveler_products`

- `id uuid PK`
- `trip_traveler_id uuid NOT NULL UNIQUE FK -> trip_travelers.id`
- `package_name text NULL`
- `room_type text NULL`
- `amount_paid_usd numeric(12,2) NULL`
- `purchased_addons_summary text NULL`
- `service_agreement_media_asset_id uuid NULL FK -> media_assets.id`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

### `trip_phases`

- `id uuid PK`
- `trip_id uuid NOT NULL FK -> trips.id`
- `parent_phase_id uuid NULL FK -> trip_phases.id`
- `phase_type text NOT NULL`
- `slug text NOT NULL`
- `title text NOT NULL`
- `subtitle text NULL`
- `icon text NULL`
- `short_description text NOT NULL`
- `detailed_description text NULL`
- `sort_order integer NOT NULL`
- `starts_at timestamptz NULL`
- `ends_at timestamptz NULL`
- `is_locked_by_default boolean NOT NULL DEFAULT false`
- `is_visible boolean NOT NULL DEFAULT true`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

Regras:

- `UNIQUE (trip_id, slug)`

Checks:

- `phase_type in ('pre_trip', 'in_trip')`

### `trip_phase_checklist_items`

- `id uuid PK`
- `trip_phase_id uuid NOT NULL FK -> trip_phases.id`
- `item_code text NOT NULL`
- `label text NOT NULL`
- `description text NULL`
- `sort_order integer NOT NULL`
- `is_required boolean NOT NULL DEFAULT false`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

Regras:

- `UNIQUE (trip_phase_id, item_code)`

### `trip_phase_links`

- `id uuid PK`
- `trip_phase_id uuid NOT NULL FK -> trip_phases.id`
- `label text NOT NULL`
- `url text NOT NULL`
- `sort_order integer NOT NULL`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

### `media_assets`

- `id uuid PK`
- `storage_provider text NOT NULL`
- `storage_bucket text NULL`
- `storage_key text NOT NULL`
- `public_url text NULL`
- `mime_type text NULL`
- `original_filename text NULL`
- `file_size_bytes bigint NULL`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

Regras:

- `UNIQUE (storage_provider, storage_key)`

### `trip_phase_attachments`

- `id uuid PK`
- `trip_phase_id uuid NOT NULL FK -> trip_phases.id`
- `media_asset_id uuid NOT NULL FK -> media_assets.id`
- `name text NOT NULL`
- `file_type text NULL`
- `sort_order integer NOT NULL`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

### `trip_activities`

- `id uuid PK`
- `trip_phase_id uuid NOT NULL FK -> trip_phases.id`
- `activity_code text NOT NULL`
- `name text NOT NULL`
- `activity_type text NOT NULL`
- `starts_at timestamptz NULL`
- `duration_minutes integer NULL`
- `short_description text NOT NULL`
- `practical_info text NULL`
- `price_label text NULL`
- `vibe text NULL`
- `sort_order integer NOT NULL`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

Regras:

- `UNIQUE (trip_phase_id, activity_code)`

Checks:

- `activity_type in ('included', 'optional', 'suggested', 'logistics')`

### `activity_media`

- `id uuid PK`
- `trip_activity_id uuid NOT NULL FK -> trip_activities.id`
- `media_asset_id uuid NOT NULL FK -> media_assets.id`
- `media_type text NOT NULL`
- `caption text NULL`
- `sort_order integer NOT NULL`
- `created_at timestamptz NOT NULL`

Checks:

- `media_type in ('image', 'video')`

### `traveler_checklist_progress`

- `id uuid PK`
- `trip_traveler_id uuid NOT NULL FK -> trip_travelers.id`
- `trip_phase_checklist_item_id uuid NOT NULL FK -> trip_phase_checklist_items.id`
- `is_completed boolean NOT NULL DEFAULT false`
- `completed_at timestamptz NULL`
- `updated_at timestamptz NOT NULL`

Regras:

- `UNIQUE (trip_traveler_id, trip_phase_checklist_item_id)`

### `traveler_phase_progress`

- `id uuid PK`
- `trip_traveler_id uuid NOT NULL FK -> trip_travelers.id`
- `trip_phase_id uuid NOT NULL FK -> trip_phases.id`
- `is_completed boolean NOT NULL DEFAULT false`
- `completed_at timestamptz NULL`
- `updated_at timestamptz NOT NULL`

Regras:

- `UNIQUE (trip_traveler_id, trip_phase_id)`

### `phase_comments`

- `id uuid PK`
- `trip_phase_id uuid NOT NULL FK -> trip_phases.id`
- `trip_traveler_id uuid NOT NULL FK -> trip_travelers.id`
- `body text NOT NULL`
- `is_private boolean NOT NULL DEFAULT false`
- `created_at timestamptz NOT NULL`
- `updated_at timestamptz NOT NULL`

### `notifications`

- `id uuid PK`
- `trip_traveler_id uuid NOT NULL FK -> trip_travelers.id`
- `title text NOT NULL`
- `body text NOT NULL`
- `notification_type text NOT NULL`
- `link_url text NULL`
- `is_read boolean NOT NULL DEFAULT false`
- `read_at timestamptz NULL`
- `created_at timestamptz NOT NULL`

Checks:

- `notification_type in ('info', 'warning', 'success', 'alert')`

## Ordem recomendada de montagem

1. `users`
2. `trips`
3. `media_assets`
4. `trip_travelers`
5. `traveler_profiles`
6. `traveler_products`
7. `trip_phases`
8. `trip_phase_checklist_items`
9. `trip_phase_links`
10. `trip_phase_attachments`
11. `trip_activities`
12. `activity_media`
13. `traveler_checklist_progress`
14. `traveler_phase_progress`
15. `phase_comments`
16. `notifications`

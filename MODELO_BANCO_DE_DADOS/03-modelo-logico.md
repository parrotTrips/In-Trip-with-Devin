# Modelo Lógico

## Entidades principais

### `users`

- `id`
- `phone`
- `full_name`
- `email`
- `status`
- `created_at`
- `updated_at`

### `trips`

- `id`
- `name`
- `short_name`
- `description`
- `start_date`
- `end_date`
- `status`
- `created_at`
- `updated_at`

### `trip_travelers`

- `id`
- `trip_id`
- `user_id`
- `created_at`
- `updated_at`

Regras:

- `trip_id + user_id` único
- representa apenas participantes da viagem

### `traveler_profiles`

- `id`
- `trip_traveler_id`
- `preferred_name`
- `date_of_birth`
- `gender`
- `passport_first_name`
- `passport_last_name`
- `passport_country`
- `passport_number`
- `passport_issue_date`
- `passport_expiration_date`
- `dietary_restrictions_flag`
- `dietary_restrictions_details`
- `seasickness_flag`
- `plus_one_flag`
- `plus_one_name`
- `plus_one_email`
- `needs_flight_help_flag`
- `flight_help_details`
- `needs_travel_insurance_help_flag`
- `unforgettable_trip_details`
- `created_at`
- `updated_at`

### `traveler_products`

- `id`
- `trip_traveler_id`
- `package_name`
- `room_type`
- `amount_paid_usd`
- `purchased_addons_summary`
- `service_agreement_media_asset_id`
- `created_at`
- `updated_at`

### `trip_phases`

- `id`
- `trip_id`
- `parent_phase_id`
- `phase_type`
- `title`
- `subtitle`
- `icon`
- `short_description`
- `detailed_description`
- `sort_order`
- `starts_at`
- `ends_at`
- `is_locked_by_default`
- `is_visible`
- `created_at`
- `updated_at`

### `trip_phase_checklist_items`

- `id`
- `trip_phase_id`
- `label`
- `description`
- `sort_order`
- `is_required`
- `created_at`
- `updated_at`

### `trip_phase_links`

- `id`
- `trip_phase_id`
- `label`
- `url`
- `sort_order`
- `created_at`
- `updated_at`

### `media_assets`

- `id`
- `drive_file_id`
- `drive_path`
- `public_url`
- `mime_type`
- `original_filename`
- `created_at`
- `updated_at`

### `trip_activities`

- `id`
- `trip_phase_id`
- `name`
- `activity_type`
- `starts_at`
- `duration_minutes`
- `short_description`
- `practical_info`
- `amount_brl`
- `sort_order`
- `created_at`
- `updated_at`

### `activity_media`

- `id`
- `trip_activity_id`
- `media_asset_id`
- `media_type`
- `caption`
- `sort_order`
- `created_at`

### `traveler_checklist_progress`

- `id`
- `trip_traveler_id`
- `trip_phase_checklist_item_id`
- `is_completed`
- `completed_at`
- `updated_at`

### `traveler_phase_progress`

- `id`
- `trip_traveler_id`
- `trip_phase_id`
- `is_completed`
- `completed_at`
- `updated_at`

## Relações principais

### Relações de catálogo

- `Trip 1:N TripPhase`
- `TripPhase 1:N TripPhaseChecklistItem`
- `TripPhase 1:N TripPhaseLink`
- `TripPhase 1:N TripActivity`
- `TripActivity 1:N ActivityMedia`
- `MediaAsset 1:N ActivityMedia`

### Relações de participação

- `User 1:N TripTraveler`
- `Trip 1:N TripTraveler`
- `TripTraveler 1:0..1 TravelerProfile`
- `TripTraveler 1:0..1 TravelerProduct`

### Relações de estado e interação

- `TripTraveler 1:N TravelerChecklistProgress`
- `TripTraveler 1:N TravelerPhaseProgress`

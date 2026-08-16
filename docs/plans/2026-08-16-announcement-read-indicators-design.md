# Announcement Read Indicators Design

## Context

Travelers currently receive staff announcements through the notifications screen. The app already has announcement creation for staff, a traveler announcements API, and bell buttons in the traveler header components. It does not persist per-traveler read state.

## Decision

Add persisted read tracking per announcement and traveler. A message is marked as read only when the traveler opens or expands that specific announcement. Opening the notifications screen alone does not mark messages as read.

## Backend Design

Create a `trip_announcement_reads` table with:

- `announcement_id`
- `user_id`
- `read_at`

The table has a unique constraint on `(announcement_id, user_id)` so marking a message as read is idempotent.

`GET /me/announcements` returns each announcement with `is_read` and an aggregate `unread_count`.

Add `POST /me/announcements/{announcement_id}/read` for travelers. The endpoint verifies that the announcement belongs to the traveler's active trip before inserting the read record.

## Frontend Design

The notification bell shows a small unread indicator when `unread_count > 0`. The notifications screen visually distinguishes unread messages. When a traveler expands an unread message, the screen calls the read endpoint, updates the card locally, and decrements the unread indicator.

## Error Handling

If marking as read fails, the announcement remains unread in local state and the traveler can retry by expanding it again. Fetch errors keep the current notifications error behavior.

## Testing

Backend tests cover:

- unread messages are returned with `is_read = false`
- expanding or marking one announcement creates a read record
- repeated mark-read calls are idempotent
- travelers cannot mark announcements from another trip

Frontend tests cover:

- unread indicator appears when unread messages exist
- expanding an unread announcement calls the read endpoint
- the unread state is removed after a successful mark-read response

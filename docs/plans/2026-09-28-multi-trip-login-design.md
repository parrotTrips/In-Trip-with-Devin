# Multi-Trip Login Design

## Context

A person may participate in more than one trip. Their role can also vary by trip: traveler on every trip, staff on every trip, or staff on some trips and traveler on others. The current application stores a global role on `users` and implicitly resolves one trip, which cannot represent this behavior safely.

The login flow must let people with multiple eligible trips select which one they want to enter after validating the OTP. People with only one eligible trip should enter it automatically. Once authenticated, they must be able to switch trips without requesting another OTP.

## Decisions

### Identity, membership, and role

- `users` represents the person's identity.
- `trip_travelers` represents their basic membership in a trip.
- A matching `trip_staff` row grants staff capabilities for that trip.
- A member present only in `trip_travelers` enters as `traveler`.
- A member present in both tables enters as `staff` and may switch to the traveler view for that same trip.
- `users.role` remains temporarily for compatibility but no longer determines the in-app role.
- Traveler and staff imports must reuse an existing user when the normalized phone number already exists.
- Staff imports continue ensuring a `trip_travelers` row exists so staff can use the traveler view.

### Eligible trips

The selector lists only trips that are current or future. Ended trips are excluded. Current trips appear first, followed by future trips ordered by nearest start date. The eligibility query must be centralized so OTP verification, listing, and trip selection use the same rule.

### Token model

Authentication has two token states:

1. A short-lived selection token is issued after OTP validation when the person has multiple eligible trips. It permits only listing and selecting that person's trips.
2. A session token is scoped to one trip and contains the user ID, trip ID, and effective role for that trip.

When exactly one eligible trip exists, OTP verification selects it automatically and returns a session token. When none exists, verification returns a `no_trips` result. Selecting or switching trips always asks the backend to issue a fresh trip-scoped session token.

The backend validates membership before issuing a session token. Staff routes additionally verify the current `trip_staff` association in the database instead of trusting only the role claim. Traveler and staff endpoints obtain the active trip from the authenticated session rather than finding an arbitrary membership.

## API Design

### `POST /auth/verify-otp`

Validates and consumes the OTP, then returns one of three outcomes:

- `no_trips`: authenticated identity has no current or future trips;
- `trip_selected`: exactly one eligible trip was selected automatically, with session token and active-trip summary;
- `selection_required`: multiple trips are available, with a short-lived selection token and trip summaries.

### `GET /auth/trips`

Returns the current eligible trips for the authenticated person. It accepts either a valid selection token or a session token so the same endpoint supports initial selection and later switching.

### `POST /auth/select-trip`

Accepts a trip identifier, confirms the person's current membership and trip eligibility, derives the per-trip role, and returns a new session token with the selected-trip summary.

## Frontend Flow

```text
Phone -> OTP -> resolve eligible trips
                  |-- none: no-access state
                  |-- one: enter automatically
                  `-- many: trip selector -> scoped session -> app
```

The trip selector displays cards with name, destination, dates, current-trip state, and a `Staff` badge where applicable. Selecting a card shows an inline loading state and enters either the staff or traveler experience according to that trip's role.

The profile/menu exposes `Trocar de viagem`. It returns to the selector without another OTP. If only one trip is eligible, the screen shows the current trip and explains that no alternatives are available.

The auth state stores the active trip ID and its summary alongside the session token and effective role. Changing trips replaces the session atomically and remounts trip-dependent providers so itinerary, travelers, announcements, profile, and staff data cannot leak across trips.

Staff enters the staff view by default and retains the existing option to preview the traveler view for the same active trip. This view toggle does not change the token or selected trip.

## Error Handling

- If a trip is removed or becomes ineligible, requests for it are refused and the person returns to the selector.
- If the identity session expires, the person returns to OTP login.
- A selection failure leaves the selector visible and allows retrying.
- Opening `Trocar de viagem` refreshes memberships, so newly added trips become available without a new OTP.
- Selecting a trip without a valid membership returns a forbidden response and never issues a scoped token.

## Compatibility and Rollout

The database associations already express most of the target model, so no new membership table is required. Existing data must be audited for duplicate identities, missing `trip_travelers` rows for staff, and inconsistent phone normalization before enabling the new flow.

During rollout, legacy tokens may be accepted only through an explicit compatibility path. They must not gain access to arbitrary trips. The frontend's existing stored auth payload should be migrated or cleared safely when it lacks an active trip.

## Testing

Automated coverage must include:

- traveler on one and multiple trips;
- staff on one and multiple trips;
- traveler on one trip and staff on another;
- automatic entry with one eligible trip;
- exclusion of ended trips and ordering of current/future trips;
- rejection of selection without membership;
- trip switching without a new OTP;
- data isolation after switching trips;
- staff/traveler view switching within one trip;
- revoked or newly added memberships;
- safe handling of legacy stored sessions and tokens.

Backend tests cover eligibility, token scopes, authorization, and route isolation. Frontend tests cover the three post-OTP outcomes, selector states, switching, persistence, remounting, and role-dependent entry.

## Rejected Alternatives

### Send a trip header on every request

This would require consistent validation across every endpoint and make accidental cross-trip access easier. A trip-scoped token provides a stronger default boundary.

### Keep selection only in the frontend

This does not fix the global-role model or prevent backend endpoints from resolving the wrong trip. It is not an adequate authorization design.

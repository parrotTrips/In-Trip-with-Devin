# Production Trip Catalog to Homologation Design

## Goal

Populate the homologation database with the complete non-personal trip catalog
from production. Homologation must contain only three human users — Marcelo
Angelo da Silva Filho, Vitor Sanches, and Luiz Becker — and all three must be
staff members of every copied trip.

## Safety boundary

The synchronization copies trip definitions and editorial content only. It
must never copy production travelers or operational and financial history.

Included data:

- trip records and trip settings;
- phases and nested phases;
- activities;
- phase checklist items and links;
- trip contacts and emergency contacts;
- recommendations, FAQs, and cancellation policies;
- other static editorial fields stored directly on the included records.

Excluded data:

- travelers, traveler profiles, documents, products, and memberships;
- bookings, payments, leads, transactions, order options, and imported phones;
- progress, activity participation, check-ins, scan events, and feedback;
- OTP codes;
- webhooks and synchronization jobs;
- announcements, announcement reads, and staff tasks.

## Approach

Implement an explicit, allowlisted, idempotent synchronization script. The
script connects to production read-only and writes to homologation. It keeps
the source identifiers for included records so foreign-key relationships remain
stable and repeated runs update homologation instead of duplicating rows.

The script has two modes:

1. Dry run: read production, validate the source graph, and print row counts by
   table without changing homologation.
2. Execute: perform the synchronization inside one homologation transaction.
   Any error rolls back the complete operation.

The execute mode replaces the homologation trip catalog rather than merging
unknown homologation-only content. This guarantees that homologation reflects
the approved production catalog after every run.

## User and staff handling

The script reads the following three identities from production by stable email
address and copies only their identity fields required for login:

- `angelo@parrottrips.com` — Marcelo Angelo da Silva Filho;
- `sanches@parrottrips.com` — Vitor Sanches;
- `becker@parrottrips.com` — Luiz Becker.

It removes other homologation users and creates one `trip_staff` membership for
each validator on every copied trip. Existing production staff memberships are
not copied. All three users are active and have the `staff` role.

## Data flow

1. Connect to production and homologation using two distinct explicit database
   URLs.
2. Refuse to run if the URLs identify the same database.
3. Resolve and validate the three staff identities in production.
4. Read all allowlisted trip catalog tables and validate references.
5. Print a source summary in dry-run mode.
6. In execute mode, open one homologation transaction.
7. Clear dependent homologation data in foreign-key-safe order.
8. Insert the allowlisted catalog in dependency order.
9. Insert the three users and the complete trip-to-staff membership matrix.
10. Verify counts and invariants before committing.

## Failure handling

- Missing or duplicate validator identities abort the run.
- A production reference outside the allowlist that is required by copied data
  aborts the run rather than silently dropping content.
- A same-database configuration aborts before any SQL mutation.
- Any count or membership invariant failure rolls back the transaction.
- Logs report table names and counts but never database URLs, passwords, phone
  numbers, OTP codes, or personal traveler data.

## Verification

Automated tests cover table allowlisting, dependency ordering, dry-run
non-mutation, same-database protection, rollback, idempotency, validator-only
users, and all-validator/all-trip membership creation.

After execution, verify directly in homologation that:

- catalog counts match production for every included table;
- there are exactly three users and all have role `staff`;
- `trip_staff` has exactly `trip count * 3` memberships;
- excluded tables contain no production traveler or operational rows;
- each validator can request an OTP and list all eligible trips.


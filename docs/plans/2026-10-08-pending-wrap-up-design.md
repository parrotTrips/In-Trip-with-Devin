# Pending and Wrap-up Design

## Goal

Make traveler phase status reflect the traveler's actual progress and ensure every production and homologation trip has a published Trip Wrap-up.

## Phase status

The backend remains the source of truth for `current_phase_id`. During pre-trip, it selects the first incomplete phase, regardless of whether later phases were completed out of order.

On the traveler journey, `Pending` appears only when a card is both the current phase and an incomplete pre-trip phase. Future incomplete phases remain neutral. Any phase completed out of order displays the existing completed badge.

The staff endpoint reports the number of incomplete pre-trip phases in both `pre-trip` and `in-trip` modes so staff can see outstanding work before departure.

## Trip Wrap-up

Use the application's existing `WRAP_UP_TEMPLATE`, checklist, and Instagram link. For every trip without a post-trip phase, create the complete phase as a draft and publish it only after its child records exist. Existing post-trip phases are left untouched, making the operation idempotent.

Apply the catalog operation independently to production and homologation. Verify counts and visibility in each database after the write.

## Verification

Add frontend tests for current, future incomplete, and future completed pre-trip cards. Add a backend test for staff pending counts during pre-trip. Run the focused tests, full frontend suite/build, and full backend suite before deploying both branches/environments.

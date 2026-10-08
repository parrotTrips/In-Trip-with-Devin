# Cancellation Policy in My Profile Design

## Goal

Bring the previously implemented cancellation-policy experience from `feat/content-console` into `main` and `homologacao` without importing unrelated Content Console work.

## Design

The traveler profile keeps package data under **Package Details & Actions** and adds **Cancellation & Transfer Policy** as the final collapsible section. The policy is fetched only when that section opens. When the selected trip has no policy records, the section shows the existing fallback message directing travelers to the trek page or signed service agreement.

The Cancellation Policy section is removed from Information so there is a single location for this flow. Existing per-trip API behavior remains unchanged.

## Integration and verification

Cherry-pick only commit `d006742`, which contains the UI change and its regression tests. Run the focused Profile and Information tests, the frontend build, then merge `main` into `homologacao` and repeat verification before pushing both branches.

# DBML ERD Design

**Context**

The repository already contains the conceptual and logical database model in `MODELO_BANCO_DE_DADOS/`. The next artifact should convert that model into a DBML file that is easy to load into ERD tooling for visual validation.

**Goal**

Create a lean DBML file that mirrors the current logical model and is optimized for quick ERD visualization.

**Approved Scope**

- Store the artifact in `docs/db/parrot-trips-erd.dbml`
- Include all current logical tables from the database modeling docs
- Keep columns, primary keys, foreign keys, and essential uniqueness/index rules
- Omit detailed `check` constraints, verbose notes, and full DDL-level defaults unless they materially affect ERD reading

**Modeling Decisions**

- Preserve UUID primary keys across all tables
- Preserve the central role of `trip_travelers` for all traveler-in-trip state
- Represent the important 1:0..1 relationships through `unique` child foreign keys
- Preserve composite uniqueness where it changes structural understanding, such as:
  - `trip_travelers (trip_id, user_id)`
  - progress tables by traveler plus tracked entity

**Output Shape**

The DBML should visually cover four blocks:

1. Identity and participation
2. Traveler profile and operational data
3. Trip catalog and media
4. Traveler progress and interaction

**Out of Scope**

- Converting the DBML into SQL migrations
- Adding analytics, secret missions, sharing XP, or other modules already marked out of scope in the model docs
- Encoding every business rule from the PostgreSQL-oriented notes

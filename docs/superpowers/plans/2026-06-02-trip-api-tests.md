# Trip API Tests — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add integration tests for the trip API endpoints (`GET /me/trip/phases`, `GET /me/trip/travelers`, `GET /me/trip`) which currently have zero test coverage.

**Architecture:** Tests follow the same pattern as existing integration tests — use `seeded_client` + `session_factory` fixtures, seed the DB with trips/phases/travelers, call the endpoints via the test client, and assert on shape and content. No new files needed in the app code.

**Tech Stack:** Python 3.13, FastAPI, pytest-asyncio, SQLAlchemy async

---

## Context

The trip API is at `backend/app/routers/trip.py`. The three untested endpoints are:
- `GET /me/trip` — returns the active trip for the authenticated user
- `GET /me/trip/phases` — returns phases with checklist and links
- `GET /me/trip/travelers` — returns travelers with `current_phase_id`

All require a JWT token (except `/admin/*`). The existing `seeded_client` fixture provides a test client with JWT middleware active. The test pattern is:
1. Use `seeded_client.post("/auth/request-otp")` → `seeded_client.post("/auth/verify-otp")` to get a token
2. Seed the DB (wetravel_trips, trip_travelers, trip_phases) via `session_factory`
3. Call the endpoint with `Authorization: Bearer <token>`
4. Assert on the response

The `TripPhase` model requires: `wetravel_trip_uuid`, `phase_type`, `title`, `short_description`, `sort_order`, `is_locked_by_default`, `is_visible`.

---

## File Map

| File | Action |
|---|---|
| `backend/tests/integration/test_trip_routes.py` | Create |

---

## Task 1: Create trip routes integration tests

**Files:**
- Create: `backend/tests/integration/test_trip_routes.py`

- [ ] **Step 1: Create the test file**

Create `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend/tests/integration/test_trip_routes.py`:

```python
"""Integration tests for GET /me/trip, /me/trip/phases and /me/trip/travelers."""

import asyncio
import uuid as _uuid

from app.db.models.trip import TripPhase, TripTraveler
from app.db.models.user import User

TEST_TRIP_UUID = "trip-routes-test-001"


# ── Seed helpers ──────────────────────────────────────────────────────────────

async def _seed_trip(session_factory, *, user_phone: str, trip_uuid: str = TEST_TRIP_UUID):
    """Create user + trip_traveler + wetravel_trips entry."""
    async with session_factory() as session:
        from sqlalchemy import text
        # Insert minimal wetravel_trips row so GET /me/trip can JOIN it
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": trip_uuid,
                "title": "Test Trip",
                "dest": "Brazil",
                "sd": "2026-07-01",
                "ed": "2026-07-10",
            },
        )
        user = User(phone=user_phone, full_name="Trip Tester", status="active")
        session.add(user)
        await session.flush()
        tt = TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=user.id)
        session.add(tt)
        await session.commit()
        return str(user.id)


async def _seed_phases(session_factory, *, trip_uuid: str = TEST_TRIP_UUID):
    """Add pre-trip and in-trip phases to the trip."""
    async with session_factory() as session:
        pre = TripPhase(
            wetravel_trip_uuid=trip_uuid,
            phase_type="pre-trip",
            title="Visa",
            subtitle="Entry requirements",
            icon="passport",
            short_description="Check visa requirements.",
            detailed_description=None,
            sort_order=0,
            starts_at=None,
            is_locked_by_default=False,
            is_visible=True,
        )
        inTrip = TripPhase(
            wetravel_trip_uuid=trip_uuid,
            phase_type="in-trip",
            title="Day 1 — Arrival",
            subtitle="Arrival",
            icon="plane-landing",
            short_description="Airport transfer.",
            detailed_description=None,
            sort_order=1,
            starts_at=None,
            is_locked_by_default=False,
            is_visible=True,
        )
        session.add_all([pre, inTrip])
        await session.commit()


def _auth(seeded_client, phone: str) -> dict:
    """Return Authorization headers for the given phone."""
    otp_res = seeded_client.post("/auth/request-otp", json={"phone": phone})
    verify_res = seeded_client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_res.json()["debug_code"]},
    )
    data = verify_res.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_get_my_trip_returns_trip_info(seeded_client, session_factory):
    """GET /me/trip returns the active trip for the authenticated user."""
    phone = "+5511333000001"
    asyncio.run(_seed_trip(session_factory, user_phone=phone))
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/trip", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["trip"] is not None
    assert data["trip"]["wetravel_trip_uuid"] == TEST_TRIP_UUID
    assert data["trip"]["title"] == "Test Trip"
    assert "start_date" in data["trip"]
    assert "end_date" in data["trip"]


def test_get_my_trip_returns_null_when_no_trip(seeded_client, session_factory):
    """GET /me/trip returns trip: null when user has no trip assignment."""
    phone = "+5511333000002"
    # Create user but DO NOT add trip_traveler row
    async def _seed_user_only():
        async with session_factory() as session:
            user = User(phone=phone, full_name="No Trip", status="active")
            session.add(user)
            await session.commit()
    asyncio.run(_seed_user_only())
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/trip", headers=headers)

    assert response.status_code == 200
    assert response.json()["trip"] is None


def test_get_my_trip_phases_returns_phases_with_checklist(seeded_client, session_factory):
    """GET /me/trip/phases returns phases with correct shape."""
    phone = "+5511333000003"
    asyncio.run(_seed_trip(session_factory, user_phone=phone))
    asyncio.run(_seed_phases(session_factory))
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/trip/phases", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "phases" in data
    assert len(data["phases"]) == 2
    phase_types = {p["phase_type"] for p in data["phases"]}
    assert phase_types == {"pre-trip", "in-trip"}
    # Each phase has required fields
    for phase in data["phases"]:
        assert "id" in phase
        assert "title" in phase
        assert "sort_order" in phase
        assert "checklist_items" in phase
        assert "links" in phase
        assert isinstance(phase["checklist_items"], list)
        assert isinstance(phase["links"], list)


def test_get_my_trip_phases_returns_404_when_no_trip(seeded_client, session_factory):
    """GET /me/trip/phases returns 404 when user has no trip assignment."""
    phone = "+5511333000004"
    async def _seed_user_only():
        async with session_factory() as session:
            user = User(phone=phone, full_name="No Trip 2", status="active")
            session.add(user)
            await session.commit()
    asyncio.run(_seed_user_only())
    headers = _auth(seeded_client, phone)

    response = seeded_client.get("/me/trip/phases", headers=headers)

    assert response.status_code == 404


def test_get_my_trip_travelers_returns_all_trip_members(seeded_client, session_factory):
    """GET /me/trip/travelers returns all travelers in the same trip."""
    phone_a = "+5511333000005"
    phone_b = "+5511333000006"
    trip_uuid = "trip-travelers-test-001"

    asyncio.run(_seed_trip(session_factory, user_phone=phone_a, trip_uuid=trip_uuid))

    # Add a second traveler to the same trip
    async def _seed_second():
        async with session_factory() as session:
            from sqlalchemy import text
            await session.execute(
                text(
                    "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                    " VALUES (:uuid, :title, :dest, :sd, :ed)"
                    " ON CONFLICT (trip_uuid) DO NOTHING"
                ),
                {"uuid": trip_uuid, "title": "Test Trip", "dest": "Brazil", "sd": "2026-07-01", "ed": "2026-07-10"},
            )
            user_b = User(phone=phone_b, full_name="Traveler B", status="active")
            session.add(user_b)
            await session.flush()
            session.add(TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=user_b.id))
            await session.commit()
    asyncio.run(_seed_second())

    headers = _auth(seeded_client, phone_a)
    response = seeded_client.get("/me/trip/travelers", headers=headers)

    assert response.status_code == 200
    travelers = response.json()["travelers"]
    phones = {t["phone"] for t in travelers}
    assert phone_a in phones
    assert phone_b in phones


def test_get_my_trip_travelers_includes_current_phase_id(seeded_client, session_factory):
    """Each traveler in the response has a current_phase_id field."""
    phone = "+5511333000007"
    trip_uuid = "trip-phase-id-test-001"

    asyncio.run(_seed_trip(session_factory, user_phone=phone, trip_uuid=trip_uuid))

    async def _seed_phase_for_trip():
        async with session_factory() as session:
            phase = TripPhase(
                wetravel_trip_uuid=trip_uuid,
                phase_type="pre-trip",
                title="Visa",
                subtitle=None,
                icon=None,
                short_description="Check requirements.",
                detailed_description=None,
                sort_order=0,
                starts_at=None,
                is_locked_by_default=False,
                is_visible=True,
            )
            session.add(phase)
            await session.commit()
    asyncio.run(_seed_phase_for_trip())

    headers = _auth(seeded_client, phone)
    response = seeded_client.get("/me/trip/travelers", headers=headers)

    assert response.status_code == 200
    travelers = response.json()["travelers"]
    assert len(travelers) >= 1
    for traveler in travelers:
        assert "current_phase_id" in traveler
        # current_phase_id points to the first incomplete phase (Visa, since nothing is completed)
        assert traveler["current_phase_id"] is not None
```

- [ ] **Step 2: Run the new tests — expect some failures due to DB setup**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run pytest tests/integration/test_trip_routes.py -v 2>&1 | tail -20
```

Expected: Some tests may fail if `wetravel_trips` table is missing from the test schema. If so, check the Alembic migrations cover this table. If the tests pass, skip Step 3.

- [ ] **Step 3: Fix if wetravel_trips is missing from test DB**

If tests fail with `table "wetravel_trips" does not exist`, check `backend/tests/conftest.py` — it runs `command.upgrade(alembic_config, "head")`. Verify that `wetravel_trips` is in the Alembic migrations by running:

```bash
poetry run alembic history --verbose 2>&1 | grep -i wetravel
```

If the table is not in migrations, the seed helper needs to use a simpler approach — store the trip_uuid directly in `trip_travelers` without the JOIN. In that case update `_seed_trip` to skip the `wetravel_trips` INSERT and update `test_get_my_trip_returns_trip_info` to only check that `trip` is not `None` (since without the JOIN row, `/me/trip` returns `trip: null`).

- [ ] **Step 4: Run all tests — no regressions**

```bash
poetry run pytest tests/ -v --ignore=tests/e2e -x 2>&1 | tail -15
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add backend/tests/integration/test_trip_routes.py
git commit -m "test: add integration tests for GET /me/trip, /me/trip/phases, /me/trip/travelers"
```

---

## Self-review

**Spec coverage:**
- ✅ `GET /me/trip` — happy path + no trip assigned
- ✅ `GET /me/trip/phases` — shape check (phase_type, checklist_items, links) + no trip 404
- ✅ `GET /me/trip/travelers` — multiple travelers + `current_phase_id` present
- ✅ No regressions in existing test suite

**Placeholder scan:** Step 3 has a conditional — handled explicitly with instructions for both cases. ✅

**Type consistency:** `_seed_trip` returns `str(user.id)` — consistent with how `user_id` is used as string throughout. ✅

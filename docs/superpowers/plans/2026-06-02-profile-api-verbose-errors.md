# Profile API Verbose Errors — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the profile PUT endpoint return detailed error messages when field parsing fails (invalid date, invalid yes/no value) and return the saved fields in the success response so the client knows what was persisted.

**Architecture:** Changes are confined to `backend/app/services/profile_service.py`. The `update_profile` function currently swallows date/yes-no parsing errors silently and returns `{"message": "Profile updated"}` with no detail. We add explicit validation before touching the DB and return `{"message": "Profile updated", "updated_fields": [...]}` on success.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy async, pytest

---

## Context

Current problems in `update_profile` (backend/app/services/profile_service.py):

1. `_parse_optional_date(value)` calls `date.fromisoformat(value)` — if the value is invalid (e.g. `"2026-13-01"`), it raises `ValueError` which propagates as an unhandled 500.
2. `_decode_yes_no(value)` returns `None` silently for any value that is not `"yes"` or `"no"` — the field is silently ignored with no feedback.
3. Success response is `{"message": "Profile updated"}` — the client cannot tell which fields were actually saved.

---

## File Map

| File | Action |
|---|---|
| `backend/app/services/profile_service.py` | Modify: add validation, improve success response |
| `backend/tests/services/test_profile_service.py` | Modify: add tests for invalid date, invalid yes/no, success response fields |

---

## Task 1: Add validation and verbose success response to update_profile

**Files:**
- Modify: `backend/app/services/profile_service.py`

- [ ] **Step 1: Write the failing tests**

Add these tests to `backend/tests/services/test_profile_service.py` (append after the existing tests):

```python
@pytest.mark.asyncio
async def test_update_profile_rejects_invalid_date_format(session_factory):
    """Invalid dob format returns 422, not 500."""
    ctx = await seed_profile_context(session_factory, phone="+5511000000010")
    async with session_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await update_profile(
                str(ctx["user"].id),
                ctx["trip_uuid"],
                {"dob": "not-a-date"},
                session,
            )
    assert exc_info.value.status_code == 422
    assert "dob" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_update_profile_rejects_invalid_yes_no_value(session_factory):
    """Invalid yes/no value returns 422 with field name in detail."""
    ctx = await seed_profile_context(session_factory, phone="+5511000000011")
    async with session_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await update_profile(
                str(ctx["user"].id),
                ctx["trip_uuid"],
                {"dietary_restrictions_yn": "maybe"},
                session,
            )
    assert exc_info.value.status_code == 422
    assert "dietary_restrictions_yn" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_update_profile_success_response_includes_updated_fields(session_factory):
    """Success response includes list of fields that were updated."""
    ctx = await seed_profile_context(session_factory, phone="+5511000000012")
    async with session_factory() as session:
        result = await update_profile(
            str(ctx["user"].id),
            ctx["trip_uuid"],
            {"preferred_name": "Lara", "gender": "female"},
            session,
        )
    assert result["message"] == "Profile updated"
    assert set(result["updated_fields"]) == {"preferred_name", "gender"}
```

Note: the tests use a `seed_profile_context` helper. Add it at the top of the test file (after imports):

```python
async def seed_profile_context(session_factory, *, phone="+5511999000000"):
    import uuid as _uuid_module
    trip_uuid = f"test_trip_{str(_uuid_module.uuid4())[:8]}"
    async with session_factory() as session:
        from app.db.models.user import User
        from app.db.models.trip import TripTraveler
        user = User(phone=phone, full_name="Test User", status="active")
        session.add(user)
        await session.flush()
        tt = TripTraveler(wetravel_trip_uuid=trip_uuid, user_id=user.id)
        session.add(tt)
        await session.commit()
        return {"user": user, "trip_uuid": trip_uuid}
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run pytest tests/services/test_profile_service.py::test_update_profile_rejects_invalid_date_format tests/services/test_profile_service.py::test_update_profile_rejects_invalid_yes_no_value tests/services/test_profile_service.py::test_update_profile_success_response_includes_updated_fields -v 2>&1 | tail -20
```

Expected: 2 fail (500 instead of 422 for date/yes-no), 1 fail (KeyError on `updated_fields`).

- [ ] **Step 3: Update `_parse_optional_date` to raise 422 on invalid format**

In `backend/app/services/profile_service.py`, replace:

```python
def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)
```

With:

```python
def _parse_optional_date(value: str | None, field_name: str = "date") -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid date format for field '{field_name}'. Expected YYYY-MM-DD, got: '{value}'",
        )
```

- [ ] **Step 4: Update `_decode_yes_no` to raise 422 on invalid value**

Replace:

```python
def _decode_yes_no(value: str | None) -> bool | None:
    if value is None:
        return None
    if value == "yes":
        return True
    if value == "no":
        return False
    return None
```

With:

```python
def _decode_yes_no(value: str | None, field_name: str = "field") -> bool | None:
    if value is None:
        return None
    if value == "yes":
        return True
    if value == "no":
        return False
    raise HTTPException(
        status_code=422,
        detail=f"Invalid value for field '{field_name}'. Expected 'yes' or 'no', got: '{value}'",
    )
```

- [ ] **Step 5: Update `update_profile` to pass field names to helpers and return updated_fields**

In `update_profile`, update all calls to `_parse_optional_date` and `_decode_yes_no` to include the field name, and change the return value. Replace the relevant block (starting at `if profile is None:` through `return {"message": "Profile updated"}`):

```python
    if profile is None:
        profile = TravelerProfile(trip_traveler_id=trip_traveler.id)
        session.add(profile)

    updated_fields: list[str] = []

    if "preferred_name" in update_data:
        profile.preferred_name = update_data["preferred_name"]
        user.full_name = update_data["preferred_name"]
        updated_fields.append("preferred_name")
    if "dob" in update_data:
        profile.date_of_birth = _parse_optional_date(update_data["dob"], "dob")
        updated_fields.append("dob")
    if "gender" in update_data:
        profile.gender = update_data["gender"]
        updated_fields.append("gender")
    if "dietary_restrictions_yn" in update_data:
        profile.dietary_restrictions_flag = _decode_yes_no(update_data["dietary_restrictions_yn"], "dietary_restrictions_yn")
        updated_fields.append("dietary_restrictions_yn")
    if "dietary_restrictions_desc" in update_data:
        profile.dietary_restrictions_details = update_data["dietary_restrictions_desc"]
        updated_fields.append("dietary_restrictions_desc")
    if "seasickness_yn" in update_data:
        profile.seasickness_flag = _decode_yes_no(update_data["seasickness_yn"], "seasickness_yn")
        updated_fields.append("seasickness_yn")
    if "first_name_passport" in update_data:
        profile.passport_first_name = update_data["first_name_passport"]
        updated_fields.append("first_name_passport")
    if "last_name_passport" in update_data:
        profile.passport_last_name = update_data["last_name_passport"]
        updated_fields.append("last_name_passport")
    if "passport_country" in update_data:
        profile.passport_country = update_data["passport_country"]
        updated_fields.append("passport_country")
    if "passport_number" in update_data:
        profile.passport_number = update_data["passport_number"]
        updated_fields.append("passport_number")
    if "passport_issue_date" in update_data:
        profile.passport_issue_date = _parse_optional_date(update_data["passport_issue_date"], "passport_issue_date")
        updated_fields.append("passport_issue_date")
    if "passport_expiration_date" in update_data:
        profile.passport_expiration_date = _parse_optional_date(update_data["passport_expiration_date"], "passport_expiration_date")
        updated_fields.append("passport_expiration_date")
    if "plus_one_yn" in update_data:
        profile.plus_one_flag = _decode_yes_no(update_data["plus_one_yn"], "plus_one_yn")
        updated_fields.append("plus_one_yn")
    if "plus_one_name" in update_data:
        profile.plus_one_name = update_data["plus_one_name"]
        updated_fields.append("plus_one_name")
    if "plus_one_email" in update_data:
        profile.plus_one_email = update_data["plus_one_email"]
        updated_fields.append("plus_one_email")
    if "intl_flights_help_yn" in update_data:
        profile.needs_flight_help_flag = _decode_yes_no(update_data["intl_flights_help_yn"], "intl_flights_help_yn")
        updated_fields.append("intl_flights_help_yn")
    if "intl_flights_help_details" in update_data:
        profile.flight_help_details = update_data["intl_flights_help_details"]
        updated_fields.append("intl_flights_help_details")
    if "travel_insurance_help_yn" in update_data:
        profile.needs_travel_insurance_help_flag = _decode_yes_no(update_data["travel_insurance_help_yn"], "travel_insurance_help_yn")
        updated_fields.append("travel_insurance_help_yn")
    if "unforgettable_trip_details" in update_data:
        profile.unforgettable_trip_details = update_data["unforgettable_trip_details"]
        updated_fields.append("unforgettable_trip_details")
    if "email" in update_data:
        user.email = update_data["email"]
        updated_fields.append("email")

    await session.commit()

    return {"message": "Profile updated", "updated_fields": updated_fields}
```

- [ ] **Step 6: Run all profile service tests — all must pass**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run pytest tests/services/test_profile_service.py -v 2>&1 | tail -15
```

Expected: all PASS (existing 4 tests + 3 new = 7 total).

- [ ] **Step 7: Run full test suite to check for regressions**

```bash
poetry run pytest tests/ -v --ignore=tests/e2e --ignore=tests/integration -x 2>&1 | tail -10
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add backend/app/services/profile_service.py backend/tests/services/test_profile_service.py
git commit -m "feat: verbose errors and updated_fields in profile update response"
```

---

## Self-review

**Spec coverage:**
- ✅ Invalid date → 422 with field name in message
- ✅ Invalid yes/no → 422 with field name in message
- ✅ Success response includes `updated_fields`
- ✅ Existing tests still pass (no breaking change to API contract — `updated_fields` is additive)

**Placeholder scan:** None.

**Type consistency:** `_parse_optional_date(value, field_name)` and `_decode_yes_no(value, field_name)` signatures are consistent with all call sites in the updated `update_profile`. ✅

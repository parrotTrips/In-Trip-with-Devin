import asyncio
from datetime import date
from uuid import UUID

from app.db.models.trip import Trip, TripPhase, TripPhaseChecklistItem, TripTraveler


async def seed_checklist_context(session_factory, *, user_id):
    async with session_factory() as session:
        trip = Trip(
            name="Ross 2026",
            short_name="ross26",
            description="Checklist integration trip",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 7),
            status="published",
        )
        session.add(trip)
        await session.flush()

        session.add(TripTraveler(trip_id=trip.id, user_id=UUID(user_id)))
        await session.flush()

        phase = TripPhase(
            trip_id=trip.id,
            phase_type="pre_trip",
            title="Before departure",
            subtitle=None,
            icon=None,
            short_description="Checklist",
            detailed_description=None,
            sort_order=1,
            starts_at=None,
            ends_at=None,
            is_locked_by_default=False,
            is_visible=True,
        )
        session.add(phase)
        await session.flush()

        item = TripPhaseChecklistItem(
            trip_phase_id=phase.id,
            label="Passport",
            description=None,
            sort_order=1,
            is_required=True,
        )
        session.add(item)
        await session.commit()

        return {
            "trip_id": str(trip.id),
            "phase_id": str(phase.id),
            "item_id": str(item.id),
        }


def create_user(client, phone="+5511991000000"):
    otp_response = client.post("/auth/request-otp", json={"phone": phone})
    verify_response = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    return verify_response.json()["user_id"]


def test_checklist_routes_persist_progress(client, session_factory):
    user_id = create_user(client)
    seeded = asyncio.run(seed_checklist_context(session_factory, user_id=user_id))

    update_response = client.post(
        f"/checklist/update?user_id={user_id}",
        json={
            "trip_id": seeded["trip_id"],
            "phase_id": seeded["phase_id"],
            "item_id": seeded["item_id"],
            "completed": True,
        },
    )
    get_response = client.get(f"/checklist/{seeded['trip_id']}/{user_id}")

    assert update_response.status_code == 200
    assert update_response.json() == {"message": "Checklist item updated"}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "trip_id": seeded["trip_id"],
        "user_id": user_id,
        "progress": {seeded["phase_id"]: {seeded["item_id"]: True}},
    }


def test_phase_routes_persist_completion(client, session_factory):
    user_id = create_user(client, phone="+5511991000001")
    seeded = asyncio.run(seed_checklist_context(session_factory, user_id=user_id))

    update_response = client.post(
        f"/phases/complete?user_id={user_id}",
        json={
            "trip_id": seeded["trip_id"],
            "phase_id": seeded["phase_id"],
            "completed": True,
        },
    )
    get_response = client.get(f"/phases/{seeded['trip_id']}/{user_id}")

    assert update_response.status_code == 200
    assert update_response.json() == {"message": "Phase completion updated"}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "trip_id": seeded["trip_id"],
        "user_id": user_id,
        "completions": {seeded["phase_id"]: True},
    }

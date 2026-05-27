import asyncio
from uuid import UUID

from app.db.models.trip import TripPhase, TripPhaseChecklistItem, TripTraveler

TEST_TRIP_UUID = "test_checklist_trip_001"


async def seed_checklist_context(session_factory, *, user_id):
    async with session_factory() as session:
        session.add(TripTraveler(wetravel_trip_uuid=TEST_TRIP_UUID, user_id=UUID(user_id)))
        await session.flush()

        phase = TripPhase(
            wetravel_trip_uuid=TEST_TRIP_UUID,
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
            "trip_id": TEST_TRIP_UUID,
            "phase_id": str(phase.id),
            "item_id": str(item.id),
        }


def create_user(seeded_client, phone="+5511991000000"):
    otp_response = seeded_client.post("/auth/request-otp", json={"phone": phone})
    verify_response = seeded_client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_response.json()["debug_code"]},
    )
    data = verify_response.json()
    return data["user_id"], data["access_token"]


def test_checklist_routes_persist_progress(seeded_client, session_factory):
    user_id, token = create_user(seeded_client)
    headers = {"Authorization": f"Bearer {token}"}
    seeded = asyncio.run(seed_checklist_context(session_factory, user_id=user_id))

    update_response = seeded_client.post(
        f"/checklist/update?user_id={user_id}",
        json={
            "trip_id": seeded["trip_id"],
            "phase_id": seeded["phase_id"],
            "item_id": seeded["item_id"],
            "completed": True,
        },
        headers=headers,
    )
    get_response = seeded_client.get(f"/checklist/{seeded['trip_id']}/{user_id}", headers=headers)

    assert update_response.status_code == 200
    assert update_response.json() == {"message": "Checklist item updated"}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "trip_id": seeded["trip_id"],
        "user_id": user_id,
        "progress": {seeded["phase_id"]: {seeded["item_id"]: True}},
    }


def test_phase_routes_persist_completion(seeded_client, session_factory):
    user_id, token = create_user(seeded_client, phone="+5511991000001")
    headers = {"Authorization": f"Bearer {token}"}
    seeded = asyncio.run(seed_checklist_context(session_factory, user_id=user_id))

    update_response = seeded_client.post(
        f"/phases/complete?user_id={user_id}",
        json={
            "trip_id": seeded["trip_id"],
            "phase_id": seeded["phase_id"],
            "completed": True,
        },
        headers=headers,
    )
    get_response = seeded_client.get(f"/phases/{seeded['trip_id']}/{user_id}", headers=headers)

    assert update_response.status_code == 200
    assert update_response.json() == {"message": "Phase completion updated"}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "trip_id": seeded["trip_id"],
        "user_id": user_id,
        "completions": {seeded["phase_id"]: True},
    }

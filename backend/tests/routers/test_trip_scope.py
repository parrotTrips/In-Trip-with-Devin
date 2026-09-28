"""Cross-trip isolation tests: every traveler API must scope to request.state.trip_id."""

import asyncio
from datetime import date

from sqlalchemy import select, text

from app.db.models.progress import TravelerChecklistProgress, TravelerPhaseProgress
from app.db.models.staff import TripAnnouncement, TripStaff
from app.db.models.traveler import TravelerProfile
from app.db.models.trip import (
    TravelerAppFeedback,
    TripCancellationPolicy,
    TripActivity,
    TripEmergencyContact,
    TripFaq,
    TripPhase,
    TripPhaseChecklistItem,
    TripRecommendation,
    TripTraveler,
)
from app.db.models.user import User

TRIP_A = "scope-trip-a"
TRIP_B = "scope-trip-b"


def _scoped_auth(user_id: str, phone: str, trip_id: str, role: str = "traveler") -> dict:
    from app.services.auth_service import _create_session_token

    token = _create_session_token(user_id, phone, trip_id, role)
    return {"Authorization": f"Bearer {token}"}


async def _seed_two_trips(session_factory):
    phone = "+5511970000001"
    other_phone = "+5511970000002"
    sender_phone = "+5511970000099"
    trip_b_staff_phone = "+5511970000098"

    async with session_factory() as session:
        user = User(phone=phone, full_name="Multi Trip Traveler", status="active")
        other_user = User(phone=other_phone, full_name="Other Trip Traveler", status="active")
        sender = User(phone=sender_phone, full_name="Sender", status="active", role="staff")
        trip_b_staff = User(
            phone=trip_b_staff_phone,
            full_name="Trip B Staff",
            status="active",
            role="staff",
        )
        session.add_all([user, other_user, sender, trip_b_staff])
        await session.flush()

        for trip_id in (TRIP_A, TRIP_B):
            await session.execute(
                text(
                    "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                    " VALUES (:trip_id, :title, 'Brazil', :sd, :ed)"
                ),
                {
                    "trip_id": trip_id,
                    "title": f"Title {trip_id}",
                    "sd": date(2027, 7, 1),
                    "ed": date(2027, 7, 10),
                },
            )

        tt_a = TripTraveler(wetravel_trip_uuid=TRIP_A, user_id=user.id)
        tt_b = TripTraveler(wetravel_trip_uuid=TRIP_B, user_id=user.id)
        tt_other_b = TripTraveler(wetravel_trip_uuid=TRIP_B, user_id=other_user.id)
        session.add_all([tt_a, tt_b, tt_other_b])
        await session.flush()

        def _phase(trip_id: str, title: str, sort_order: int) -> TripPhase:
            return TripPhase(
                wetravel_trip_uuid=trip_id,
                phase_type="pre-trip",
                title=title,
                subtitle=None,
                icon=None,
                short_description=f"{title} description",
                detailed_description=None,
                sort_order=sort_order,
                starts_at=None,
                is_locked_by_default=False,
                is_visible=True,
            )

        phase_a = _phase(TRIP_A, "Trip A phase", 0)
        phase_b = _phase(TRIP_B, "Trip B phase", 0)
        session.add_all([phase_a, phase_b])
        await session.flush()

        item_a = TripPhaseChecklistItem(
            trip_phase_id=phase_a.id, label="Item A", description=None, sort_order=0, is_required=True
        )
        item_b = TripPhaseChecklistItem(
            trip_phase_id=phase_b.id, label="Item B", description=None, sort_order=0, is_required=True
        )
        session.add_all([item_a, item_b])
        await session.flush()

        activity_a = TripActivity(
            trip_phase_id=phase_a.id,
            name="Activity A",
            activity_type="tour",
            short_description="Only in trip A",
            max_checkins=1,
            sort_order=0,
        )
        activity_b = TripActivity(
            trip_phase_id=phase_b.id,
            name="Activity B",
            activity_type="tour",
            short_description="Only in trip B",
            max_checkins=1,
            sort_order=0,
        )
        session.add_all([activity_a, activity_b])

        session.add_all(
            [
                TripStaff(
                    wetravel_trip_uuid=TRIP_A,
                    user_id=sender.id,
                    function="Trip A host",
                ),
                TripStaff(
                    wetravel_trip_uuid=TRIP_B,
                    user_id=trip_b_staff.id,
                    function="Trip B host",
                ),
            ]
        )

        ann_a = TripAnnouncement(
            wetravel_trip_uuid=TRIP_A, title="A news", body="A body", sent_by_user_id=sender.id
        )
        ann_b = TripAnnouncement(
            wetravel_trip_uuid=TRIP_B, title="B news", body="B body", sent_by_user_id=sender.id
        )
        session.add_all([ann_a, ann_b])

        session.add_all(
            [
                TripEmergencyContact(
                    wetravel_trip_uuid=TRIP_A, name="A Contact", role="Guide", phone="+1", sort_order=0
                ),
                TripEmergencyContact(
                    wetravel_trip_uuid=TRIP_B, name="B Contact", role="Guide", phone="+2", sort_order=0
                ),
                TripRecommendation(wetravel_trip_uuid=TRIP_A, name="A Rec", sort_order=0),
                TripRecommendation(wetravel_trip_uuid=TRIP_B, name="B Rec", sort_order=0),
                TripFaq(wetravel_trip_uuid=TRIP_A, question="A?", answer="A!", sort_order=0),
                TripFaq(wetravel_trip_uuid=TRIP_B, question="B?", answer="B!", sort_order=0),
                TripCancellationPolicy(wetravel_trip_uuid=TRIP_A, title="A Policy", body="A body", sort_order=0),
                TripCancellationPolicy(wetravel_trip_uuid=TRIP_B, title="B Policy", body="B body", sort_order=0),
            ]
        )

        session.add_all(
            [
                TravelerProfile(trip_traveler_id=tt_a.id, preferred_name="Name A"),
                TravelerProfile(trip_traveler_id=tt_b.id, preferred_name="Name B"),
            ]
        )

        await session.commit()

        return {
            "user_id": str(user.id),
            "phone": phone,
            "other_user_id": str(other_user.id),
            "trip_a": TRIP_A,
            "trip_b": TRIP_B,
            "trip_traveler_a_id": str(tt_a.id),
            "trip_traveler_b_id": str(tt_b.id),
            "phase_a_id": str(phase_a.id),
            "phase_b_id": str(phase_b.id),
            "checklist_item_a_id": str(item_a.id),
            "checklist_item_b_id": str(item_b.id),
            "activity_a_id": str(activity_a.id),
            "activity_b_id": str(activity_b.id),
            "announcement_a_id": str(ann_a.id),
            "announcement_b_id": str(ann_b.id),
        }


def test_me_trip_returns_selected_trip_only(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/trip", headers=headers)

    assert response.status_code == 200
    assert response.json()["trip"]["wetravel_trip_uuid"] == seed["trip_b"]


def test_me_qr_code_uses_selected_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/qr-code", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["trip_uuid"] == seed["trip_b"]
    assert data["trip_traveler_id"] == seed["trip_traveler_b_id"]


def test_me_trip_phases_returns_only_selected_trip_phase(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/trip/phases", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["wetravel_trip_uuid"] == seed["trip_b"]
    assert [p["id"] for p in data["phases"]] == [seed["phase_b_id"]]


def test_me_trip_phase_detail_rejects_other_trip_phase(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    own = seeded_client.get(f"/me/trip/phases/{seed['phase_b_id']}", headers=headers)
    cross = seeded_client.get(f"/me/trip/phases/{seed['phase_a_id']}", headers=headers)

    assert own.status_code == 200
    assert [activity["id"] for activity in own.json()["activities"]] == [
        seed["activity_b_id"]
    ]
    assert seed["activity_a_id"] not in {
        activity["id"] for activity in own.json()["activities"]
    }
    assert cross.status_code == 404


def test_me_trip_travelers_returns_only_selected_trip_members(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/trip/travelers", headers=headers)

    assert response.status_code == 200
    ids = {t["id"] for t in response.json()["travelers"]}
    assert ids == {seed["user_id"], seed["other_user_id"]}


def test_me_team_returns_only_selected_trip_staff(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/team", headers=headers)

    assert response.status_code == 200
    assert [(member["name"], member["function"]) for member in response.json()["team"]] == [
        ("Trip B Staff", "Trip B host")
    ]


def test_me_announcements_isolated_to_selected_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/announcements", headers=headers)

    assert response.status_code == 200
    titles = {a["title"] for a in response.json()["announcements"]}
    assert titles == {"B news"}


def test_mark_announcement_read_rejects_other_trip_announcement(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.post(f"/me/announcements/{seed['announcement_a_id']}/read", headers=headers)

    assert response.status_code == 404


def test_me_emergency_contacts_isolated_to_selected_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/emergency-contacts", headers=headers)

    assert response.status_code == 200
    names = {c["name"] for c in response.json()["emergency_contacts"]}
    assert names == {"B Contact"}


def test_me_recommendations_isolated_to_selected_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/recommendations", headers=headers)

    assert response.status_code == 200
    names = {r["name"] for r in response.json()["recommendations"]}
    assert names == {"B Rec"}


def test_me_faq_isolated_to_selected_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/faq", headers=headers)

    assert response.status_code == 200
    questions = {f["question"] for f in response.json()["faq"]}
    assert questions == {"B?"}


def test_me_cancellation_policy_isolated_to_selected_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.get("/me/cancellation-policy", headers=headers)

    assert response.status_code == 200
    titles = {p["title"] for p in response.json()["cancellation_policy"]}
    assert titles == {"B Policy"}


def test_me_app_feedback_attaches_to_selected_trip_traveler(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.post(
        "/me/app-feedback", headers=headers, json={"feedback": "Great trip so far"}
    )

    assert response.status_code == 200

    async def _load_owner():
        async with session_factory() as session:
            feedback = await session.scalar(
                select(TravelerAppFeedback).where(TravelerAppFeedback.id == response.json()["id"])
            )
            return str(feedback.trip_traveler_id)

    assert asyncio.run(_load_owner()) == seed["trip_traveler_b_id"]


def test_profile_route_rejects_trip_id_and_user_id_mismatch(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    own = seeded_client.get(f"/profile/{seed['user_id']}", headers=headers)
    wrong_trip_query = seeded_client.get(
        f"/profile/{seed['user_id']}?trip_id={seed['trip_a']}", headers=headers
    )
    wrong_user = seeded_client.get(f"/profile/{seed['other_user_id']}", headers=headers)

    assert own.status_code == 200
    assert own.json()["wetravel_trip_uuid"] == seed["trip_b"]
    assert own.json()["profile"]["preferred_name"] == "Name B"
    assert wrong_trip_query.status_code == 403
    assert wrong_user.status_code == 403


def test_profile_update_ignores_caller_trip_id_and_uses_selected_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.put(
        f"/profile/{seed['user_id']}?trip_id={seed['trip_a']}",
        json={"preferred_name": "Should 403"},
        headers=headers,
    )

    assert response.status_code == 403

    async def _profile_a_untouched():
        async with session_factory() as session:
            profile = await session.scalar(
                select(TravelerProfile).where(
                    TravelerProfile.trip_traveler_id == seed["trip_traveler_a_id"]
                )
            )
            return profile.preferred_name

    assert asyncio.run(_profile_a_untouched()) == "Name A"


def test_profile_update_changes_only_selected_trip_profile(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    response = seeded_client.put(
        f"/profile/{seed['user_id']}",
        json={"preferred_name": "Updated B"},
        headers=headers,
    )

    assert response.status_code == 200

    async def _load_names():
        async with session_factory() as session:
            rows = await session.execute(
                select(TravelerProfile.trip_traveler_id, TravelerProfile.preferred_name).where(
                    TravelerProfile.trip_traveler_id.in_(
                        [seed["trip_traveler_a_id"], seed["trip_traveler_b_id"]]
                    )
                )
            )
            return {str(trip_traveler_id): name for trip_traveler_id, name in rows.all()}

    assert asyncio.run(_load_names()) == {
        seed["trip_traveler_a_id"]: "Name A",
        seed["trip_traveler_b_id"]: "Updated B",
    }


def test_staff_session_can_use_traveler_view_for_selected_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))

    async def _assign_staff_role():
        async with session_factory() as session:
            session.add(
                TripStaff(
                    wetravel_trip_uuid=seed["trip_b"],
                    user_id=seed["user_id"],
                    function="Traveler-facing host",
                )
            )
            await session.commit()

    asyncio.run(_assign_staff_role())
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"], role="staff")

    response = seeded_client.get("/me/trip", headers=headers)

    assert response.status_code == 200
    assert response.json()["trip"]["wetravel_trip_uuid"] == seed["trip_b"]


def test_trip_travelers_roommate_route_rejects_other_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    own = seeded_client.get(f"/trip/{seed['trip_b']}/travelers", headers=headers)
    cross = seeded_client.get(f"/trip/{seed['trip_a']}/travelers", headers=headers)

    assert own.status_code == 200
    assert cross.status_code == 403


def test_trip_travelers_roommate_route_rejects_revoked_membership(
    seeded_client, session_factory
):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    async def _revoke_membership():
        async with session_factory() as session:
            profile = await session.scalar(
                select(TravelerProfile).where(
                    TravelerProfile.trip_traveler_id == seed["trip_traveler_b_id"]
                )
            )
            await session.delete(profile)
            membership = await session.get(TripTraveler, seed["trip_traveler_b_id"])
            await session.delete(membership)
            await session.commit()

    asyncio.run(_revoke_membership())

    response = seeded_client.get(f"/trip/{seed['trip_b']}/travelers", headers=headers)

    assert response.status_code == 403


def test_checklist_update_rejects_cross_trip_and_cross_user(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    cross_trip = seeded_client.post(
        f"/checklist/update?user_id={seed['user_id']}",
        json={
            "trip_id": seed["trip_a"],
            "phase_id": seed["phase_a_id"],
            "item_id": seed["checklist_item_a_id"],
            "completed": True,
        },
        headers=headers,
    )
    cross_user = seeded_client.post(
        f"/checklist/update?user_id={seed['other_user_id']}",
        json={
            "trip_id": seed["trip_b"],
            "phase_id": seed["phase_b_id"],
            "item_id": seed["checklist_item_b_id"],
            "completed": True,
        },
        headers=headers,
    )
    own = seeded_client.post(
        f"/checklist/update?user_id={seed['user_id']}",
        json={
            "trip_id": seed["trip_b"],
            "phase_id": seed["phase_b_id"],
            "item_id": seed["checklist_item_b_id"],
            "completed": True,
        },
        headers=headers,
    )

    assert cross_trip.status_code == 403
    assert cross_user.status_code == 403
    assert own.status_code == 200


def test_checklist_progress_route_rejects_cross_trip_and_cross_user(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    cross_trip = seeded_client.get(f"/checklist/{seed['trip_a']}/{seed['user_id']}", headers=headers)
    cross_user = seeded_client.get(f"/checklist/{seed['trip_b']}/{seed['other_user_id']}", headers=headers)
    own = seeded_client.get(f"/checklist/{seed['trip_b']}/{seed['user_id']}", headers=headers)

    assert cross_trip.status_code == 403
    assert cross_user.status_code == 403
    assert own.status_code == 200


def test_phase_completion_rejects_cross_trip(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    cross_trip = seeded_client.post(
        f"/phases/complete?user_id={seed['user_id']}",
        json={"trip_id": seed["trip_a"], "phase_id": seed["phase_a_id"], "completed": True},
        headers=headers,
    )
    own = seeded_client.post(
        f"/phases/complete?user_id={seed['user_id']}",
        json={"trip_id": seed["trip_b"], "phase_id": seed["phase_b_id"], "completed": True},
        headers=headers,
    )

    assert cross_trip.status_code == 403
    assert own.status_code == 200


def test_phase_completions_route_rejects_cross_trip_and_cross_user(seeded_client, session_factory):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    cross_trip = seeded_client.get(f"/phases/{seed['trip_a']}/{seed['user_id']}", headers=headers)
    cross_user = seeded_client.get(f"/phases/{seed['trip_b']}/{seed['other_user_id']}", headers=headers)
    own = seeded_client.get(f"/phases/{seed['trip_b']}/{seed['user_id']}", headers=headers)

    assert cross_trip.status_code == 403
    assert cross_user.status_code == 403
    assert own.status_code == 200


def test_progress_reads_exclude_inconsistent_records_from_other_trip(
    seeded_client, session_factory
):
    seed = asyncio.run(_seed_two_trips(session_factory))
    headers = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_b"])

    async def _seed_progress():
        async with session_factory() as session:
            session.add_all(
                [
                    TravelerChecklistProgress(
                        trip_traveler_id=seed["trip_traveler_a_id"],
                        trip_phase_checklist_item_id=seed["checklist_item_a_id"],
                        is_completed=False,
                    ),
                    TravelerChecklistProgress(
                        trip_traveler_id=seed["trip_traveler_b_id"],
                        trip_phase_checklist_item_id=seed["checklist_item_b_id"],
                        is_completed=True,
                    ),
                    TravelerChecklistProgress(
                        trip_traveler_id=seed["trip_traveler_b_id"],
                        trip_phase_checklist_item_id=seed["checklist_item_a_id"],
                        is_completed=False,
                    ),
                    TravelerPhaseProgress(
                        trip_traveler_id=seed["trip_traveler_a_id"],
                        trip_phase_id=seed["phase_a_id"],
                        is_completed=False,
                    ),
                    TravelerPhaseProgress(
                        trip_traveler_id=seed["trip_traveler_b_id"],
                        trip_phase_id=seed["phase_b_id"],
                        is_completed=True,
                    ),
                    TravelerPhaseProgress(
                        trip_traveler_id=seed["trip_traveler_b_id"],
                        trip_phase_id=seed["phase_a_id"],
                        is_completed=False,
                    ),
                ]
            )
            await session.commit()

    asyncio.run(_seed_progress())

    headers_a = _scoped_auth(seed["user_id"], seed["phone"], seed["trip_a"])
    checklist_a = seeded_client.get(
        f"/checklist/{seed['trip_a']}/{seed['user_id']}", headers=headers_a
    )
    phases_a = seeded_client.get(
        f"/phases/{seed['trip_a']}/{seed['user_id']}", headers=headers_a
    )
    checklist = seeded_client.get(
        f"/checklist/{seed['trip_b']}/{seed['user_id']}", headers=headers
    )
    phases = seeded_client.get(
        f"/phases/{seed['trip_b']}/{seed['user_id']}", headers=headers
    )

    assert checklist_a.status_code == 200
    assert checklist_a.json()["progress"] == {
        seed["phase_a_id"]: {seed["checklist_item_a_id"]: False}
    }
    assert phases_a.status_code == 200
    assert phases_a.json()["completions"] == {seed["phase_a_id"]: False}
    assert checklist.status_code == 200
    assert checklist.json()["progress"] == {
        seed["phase_b_id"]: {seed["checklist_item_b_id"]: True}
    }
    assert phases.status_code == 200
    assert phases.json()["completions"] == {seed["phase_b_id"]: True}

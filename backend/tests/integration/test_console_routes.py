import asyncio
from datetime import date

from sqlalchemy import text

from app.db.models.user import User


async def _seed_admin_and_trip(session_factory):
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                " VALUES (:uuid, :title, :dest, :sd, :ed)"
                " ON CONFLICT (trip_uuid) DO NOTHING"
            ),
            {
                "uuid": "console-test",
                "title": "Console Test Trip",
                "dest": "Brazil",
                "sd": date(2027, 7, 1),
                "ed": date(2027, 7, 10),
            },
        )
        session.add_all([
            User(phone="+5511777000001", full_name="Admin", status="active", role="admin"),
            User(phone="+5511777000002", full_name="Trav", status="active", role="traveler"),
        ])
        await session.commit()


def _auth(client, phone: str) -> dict:
    otp_res = client.post("/auth/request-otp", json={"phone": phone})
    verify_res = client.post(
        "/auth/verify-otp",
        json={"phone": phone, "code": otp_res.json()["debug_code"]},
    )
    return {"Authorization": f"Bearer {verify_res.json()['access_token']}"}


def test_console_trips_requires_a_token(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    assert client.get("/console/trips").status_code == 401


def test_console_trips_rejects_non_admin(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000002")
    assert client.get("/console/trips", headers=headers).status_code == 403


def test_console_trips_lists_trips_for_admin(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    res = client.get("/console/trips", headers=headers)
    assert res.status_code == 200
    assert "console-test" in [t["trip_uuid"] for t in res.json()["trips"]]


async def _seed_phase_with_children(session_factory):
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO trip_phases
                    (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                     short_description, detailed_description, sort_order,
                     is_locked_by_default, is_visible, created_at, updated_at)
                VALUES (gen_random_uuid(), 'console-test', 'pre-trip', 'Documentos', 'sub',
                        'passport', 'curta', 'longa', 0, false, true, now(), now())
            """)
        )
        phase_id = await session.scalar(
            text("SELECT id FROM trip_phases WHERE wetravel_trip_uuid='console-test' LIMIT 1")
        )
        await session.execute(
            text("""
                INSERT INTO trip_phase_checklist_items
                    (id, trip_phase_id, label, sort_order, is_required, created_at, updated_at)
                VALUES (gen_random_uuid(), :pid, 'Passaporte', 0, true, now(), now())
            """),
            {"pid": phase_id},
        )
        await session.execute(
            text("""
                INSERT INTO trip_phase_links
                    (id, trip_phase_id, label, url, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), :pid, 'Portal', 'https://example.com', 0, now(), now())
            """),
            {"pid": phase_id},
        )
        await session.commit()


def test_get_phases_returns_checklist_and_links(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")

    res = client.get("/console/trips/console-test/phases", headers=headers)

    assert res.status_code == 200
    phases = res.json()["phases"]
    assert len(phases) == 1
    assert phases[0]["title"] == "Documentos"
    assert phases[0]["is_visible"] is True
    assert [i["label"] for i in phases[0]["checklist"]] == ["Passaporte"]
    assert [link["url"] for link in phases[0]["links"]] == ["https://example.com"]


def test_created_phase_starts_invisible_to_travelers(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")

    res = client.post(
        "/console/trips/console-test/phases",
        headers=headers,
        json={"title": "Nova Fase", "short_description": "curta"},
    )

    assert res.status_code == 200
    assert res.json()["is_visible"] is False

    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert [p["title"] for p in phases] == ["Nova Fase"]

    async def _count_visible():
        async with session_factory() as session:
            return await session.scalar(
                text("""
                    SELECT count(*) FROM trip_phases
                    WHERE wetravel_trip_uuid='console-test' AND is_visible IS TRUE
                """)
            )

    assert asyncio.run(_count_visible()) == 0


def test_patch_phase_updates_only_provided_fields(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.post(
        "/console/trips/console-test/phases",
        headers=headers,
        json={"title": "Antigo", "short_description": "curta"},
    ).json()["id"]

    res = client.patch(f"/console/phases/{phase_id}", headers=headers, json={"title": "Novo"})

    assert res.status_code == 200
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert phases[0]["title"] == "Novo"
    assert phases[0]["short_description"] == "curta"


def test_publish_and_unpublish_toggle_visibility(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.post(
        "/console/trips/console-test/phases",
        headers=headers,
        json={"title": "Fase", "short_description": "curta"},
    ).json()["id"]

    assert client.post(
        f"/console/phases/{phase_id}/publish", headers=headers
    ).json()["is_visible"] is True
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert phases[0]["is_visible"] is True

    assert client.post(
        f"/console/phases/{phase_id}/unpublish", headers=headers
    ).json()["is_visible"] is False
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert phases[0]["is_visible"] is False


def test_delete_phase_removes_checklist_and_links(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["id"]

    assert client.delete(f"/console/phases/{phase_id}", headers=headers).status_code == 200

    async def _counts():
        async with session_factory() as session:
            return (
                await session.scalar(
                    text("SELECT count(*) FROM trip_phases WHERE id = CAST(:p AS uuid)"),
                    {"p": phase_id},
                ),
                await session.scalar(
                    text("SELECT count(*) FROM trip_phase_checklist_items"
                         " WHERE trip_phase_id = CAST(:p AS uuid)"),
                    {"p": phase_id},
                ),
                await session.scalar(
                    text("SELECT count(*) FROM trip_phase_links"
                         " WHERE trip_phase_id = CAST(:p AS uuid)"),
                    {"p": phase_id},
                ),
            )

    assert asyncio.run(_counts()) == (0, 0, 0)


def test_delete_phase_refuses_when_activities_exist(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["id"]

    async def _add_activity():
        async with session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO trip_activities
                        (id, trip_phase_id, name, activity_type, short_description,
                         practical_info, sort_order, created_at, updated_at)
                    VALUES (gen_random_uuid(), CAST(:p AS uuid), 'Atividade', 'included',
                            '', '', 0, now(), now())
                """),
                {"p": phase_id},
            )
            await session.commit()

    asyncio.run(_add_activity())

    res = client.delete(f"/console/phases/{phase_id}", headers=headers)

    assert res.status_code == 409

    async def _still_there():
        async with session_factory() as session:
            return await session.scalar(
                text("SELECT count(*) FROM trip_phases WHERE id = CAST(:p AS uuid)"),
                {"p": phase_id},
            )

    assert asyncio.run(_still_there()) == 1


def test_put_checklist_replaces_list_and_sets_order(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["id"]

    res = client.put(
        f"/console/phases/{phase_id}/checklist",
        headers=headers,
        json={"items": [
            {"label": "Segundo", "is_required": False},
            {"label": "Primeiro", "is_required": True},
        ]},
    )

    assert res.status_code == 200
    assert res.json()["count"] == 2
    checklist = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["checklist"]
    assert [i["label"] for i in checklist] == ["Segundo", "Primeiro"]
    assert [i["sort_order"] for i in checklist] == [0, 1]
    assert [i["is_required"] for i in checklist] == [False, True]


def test_put_links_replaces_list(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    asyncio.run(_seed_phase_with_children(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["id"]

    res = client.put(
        f"/console/phases/{phase_id}/links",
        headers=headers,
        json={"links": [{"label": "Novo", "url": "https://novo.example.com"}]},
    )

    assert res.status_code == 200
    links = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]["links"]
    assert [link["label"] for link in links] == ["Novo"]

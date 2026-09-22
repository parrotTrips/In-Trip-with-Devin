import asyncio
from datetime import date

import pytest
from sqlalchemy import text


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
        await session.commit()


def _auth(client, phone: str) -> dict:
    del client, phone
    return {}


def test_console_trips_requires_a_google_token(client, session_factory, monkeypatch):
    asyncio.run(_seed_admin_and_trip(session_factory))
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "false")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client.apps.googleusercontent.com")
    assert client.get("/console/trips").status_code == 401


def test_console_accepts_workspace_identity_without_database_user(
    client, session_factory, monkeypatch
):
    from app.core import console_auth

    asyncio.run(_seed_admin_and_trip(session_factory))
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "false")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client.apps.googleusercontent.com")
    monkeypatch.setattr(console_auth, "_verify_google_token_sync", lambda *_: {
        "sub": "workspace-user", "email": "user@parrottrips.com",
        "email_verified": True, "hd": "parrottrips.com",
    })

    response = client.get(
        "/console/trips", headers={"Authorization": "Bearer google-id-token"}
    )

    assert response.status_code == 200
    assert "console-test" in [trip["trip_uuid"] for trip in response.json()["trips"]]


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("GET", "/console/trips", None),
        ("GET", "/console/trips/trip/phases", None),
        ("POST", "/console/trips/trip/phases", {"title": "F", "short_description": "D"}),
        ("PATCH", "/console/phases/00000000-0000-0000-0000-000000000000", {"title": "F"}),
        ("POST", "/console/phases/00000000-0000-0000-0000-000000000000/publish", None),
        ("DELETE", "/console/phases/00000000-0000-0000-0000-000000000000", None),
        ("PUT", "/console/phases/00000000-0000-0000-0000-000000000000/checklist", {"items": []}),
        ("PUT", "/console/phases/00000000-0000-0000-0000-000000000000/links", {"links": []}),
        ("PUT", "/console/trips/trip/phases/order", {"phase_ids": []}),
    ],
)
def test_every_console_route_rejects_missing_google_token(
    client, monkeypatch, method, path, json
):
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "false")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client.apps.googleusercontent.com")
    assert client.request(method, path, json=json).status_code == 401


def test_console_trips_lists_trips_for_admin(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    res = client.get("/console/trips", headers=headers)
    assert res.status_code == 200
    assert "console-test" in [t["trip_uuid"] for t in res.json()["trips"]]


async def _seed_phase_with_children(session_factory, *, is_visible=True):
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO trip_phases
                    (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                     short_description, detailed_description, sort_order,
                     is_locked_by_default, is_visible, created_at, updated_at)
                VALUES (gen_random_uuid(), 'console-test', 'pre-trip', 'Documentos', 'sub',
                        'passport', 'curta', 'longa', 0, false, :is_visible, now(), now())
            """),
            {"is_visible": is_visible},
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
    asyncio.run(_seed_phase_with_children(session_factory, is_visible=False))
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
    asyncio.run(_seed_phase_with_children(session_factory, is_visible=False))
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
    asyncio.run(_seed_phase_with_children(session_factory, is_visible=False))
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
    asyncio.run(_seed_phase_with_children(session_factory, is_visible=False))
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


def test_reorder_phases_sets_sort_order_by_position(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    first = client.post("/console/trips/console-test/phases", headers=headers,
                        json={"title": "A", "short_description": "Descrição A"}).json()["id"]
    second = client.post("/console/trips/console-test/phases", headers=headers,
                         json={"title": "B", "short_description": "Descrição B"}).json()["id"]

    res = client.put(
        "/console/trips/console-test/phases/order",
        headers=headers,
        json={"phase_ids": [second, first]},
    )

    assert res.status_code == 200
    phases = client.get("/console/trips/console-test/phases", headers=headers).json()["phases"]
    assert [p["title"] for p in phases] == ["B", "A"]


def test_phase_dates_can_be_set_and_cleared(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    headers = _auth(client, "+5511777000001")
    phase_id = client.post(
        "/console/trips/console-test/phases",
        headers=headers,
        json={"title": "Fase com data", "short_description": "Descrição"},
    ).json()["id"]

    res = client.patch(
        f"/console/phases/{phase_id}",
        headers=headers,
        json={"starts_at": "2027-07-01T09:00:00-03:00", "ends_at": "2027-07-02T18:00:00-03:00"},
    )

    assert res.status_code == 200
    phase = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]
    assert phase["starts_at"].startswith("2027-07-01T12:00")
    assert phase["ends_at"].startswith("2027-07-02T21:00")

    clear = client.patch(f"/console/phases/{phase_id}", headers=headers,
                         json={"starts_at": None, "ends_at": None})

    assert clear.status_code == 200
    phase = client.get(
        "/console/trips/console-test/phases", headers=headers
    ).json()["phases"][0]
    assert phase["starts_at"] is None
    assert phase["ends_at"] is None


def _create_phase(client, *, title="Rascunho") -> str:
    response = client.post(
        "/console/trips/console-test/phases",
        json={"title": title, "short_description": "Descrição curta"},
    )
    assert response.status_code == 200
    return response.json()["id"]


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("PATCH", "", {"title": "Alterado"}),
        ("PUT", "/checklist", {"items": [{"label": "Item", "is_required": True}]}),
        ("PUT", "/links", {"links": [{"label": "Site", "url": "https://example.com"}]}),
        ("DELETE", "", None),
    ],
)
def test_published_phase_cannot_be_changed(client, session_factory, method, suffix, body):
    asyncio.run(_seed_admin_and_trip(session_factory))
    phase_id = _create_phase(client)
    assert client.post(f"/console/phases/{phase_id}/publish").status_code == 200

    response = client.request(method, f"/console/phases/{phase_id}{suffix}", json=body)

    assert response.status_code == 409
    assert response.json()["detail"] == "Unpublish the phase before changing it"


def test_reordering_published_phases_is_rejected(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    first = _create_phase(client, title="A")
    second = _create_phase(client, title="B")
    client.post(f"/console/phases/{first}/publish")

    response = client.put(
        "/console/trips/console-test/phases/order", json={"phase_ids": [second, first]}
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "short_description": "Descrição"},
        {"title": "Fase", "short_description": "   "},
    ],
)
def test_empty_required_phase_fields_are_rejected(client, session_factory, payload):
    asyncio.run(_seed_admin_and_trip(session_factory))
    response = client.post("/console/trips/console-test/phases", json=payload)
    assert response.status_code == 422


def test_atomic_save_rejects_invalid_url_and_inverted_dates(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    phase_id = _create_phase(client)
    payload = {
        "title": "Rascunho",
        "short_description": "Descrição",
        "checklist": [],
        "links": [{"label": "Arquivo", "url": "ftp://example.com/file"}],
        "starts_at": "2027-07-02T10:00:00Z",
        "ends_at": "2027-07-01T10:00:00Z",
    }

    assert client.put(f"/console/phases/{phase_id}/content", json=payload).status_code == 422
    payload["links"] = [{"label": "Arquivo", "url": "https://example.com/file"}]
    assert client.put(f"/console/phases/{phase_id}/content", json=payload).status_code == 422


def test_atomic_save_updates_phase_and_children(client, session_factory):
    asyncio.run(_seed_admin_and_trip(session_factory))
    phase_id = _create_phase(client)

    response = client.put(
        f"/console/phases/{phase_id}/content",
        json={
            "title": "Documentos",
            "subtitle": "Antes de viajar",
            "icon": "passport",
            "short_description": "Prepare os documentos",
            "detailed_description": "Confira tudo.",
            "starts_at": "2027-07-01T09:00:00-03:00",
            "ends_at": "2027-07-02T18:00:00-03:00",
            "checklist": [{"label": "Passaporte", "is_required": True}],
            "links": [{"label": "Portal", "url": "https://example.com"}],
        },
    )

    assert response.status_code == 200
    phase = client.get("/console/trips/console-test/phases").json()["phases"][0]
    assert phase["title"] == "Documentos"
    assert [item["label"] for item in phase["checklist"]] == ["Passaporte"]
    assert [link["url"] for link in phase["links"]] == ["https://example.com/"]


def test_atomic_save_rolls_back_phase_when_children_fail(
    client, session_factory, monkeypatch
):
    from app.services import console_service

    asyncio.run(_seed_admin_and_trip(session_factory))
    phase_id = _create_phase(client, title="Original")

    async def fail_children(*_args, **_kwargs):
        raise RuntimeError("controlled child failure")

    monkeypatch.setattr(console_service, "_replace_phase_children", fail_children, raising=False)
    with pytest.raises(RuntimeError, match="controlled child failure"):
        client.put(
            f"/console/phases/{phase_id}/content",
            json={
                "title": "Não pode persistir",
                "short_description": "Descrição",
                "checklist": [],
                "links": [],
            },
        )

    phase = client.get("/console/trips/console-test/phases").json()["phases"][0]
    assert phase["title"] == "Original"

import asyncio
from datetime import date

from sqlalchemy import text

from app.db.models.user import User

TRIP = "sections-test"
OTHER_TRIP = "sections-other"


async def _seed(session_factory):
    """One trip with a little of everything, plus a second trip to prove filtering."""
    async with session_factory() as session:
        for uuid_, title in ((TRIP, "Sections Test"), (OTHER_TRIP, "Other Trip")):
            await session.execute(
                text(
                    "INSERT INTO wetravel_trips (trip_uuid, title, destination, start_date, end_date)"
                    " VALUES (:u, :t, 'Brazil', :sd, :ed) ON CONFLICT (trip_uuid) DO NOTHING"
                ),
                {"u": uuid_, "t": title, "sd": date(2027, 7, 1), "ed": date(2027, 7, 10)},
            )

        admin = User(phone="+5511666000001", full_name="Admin", status="active", role="admin")
        traveler = User(
            phone="+5511666000002", full_name="Ana Viajante", status="active", role="traveler"
        )
        staff_user = User(
            phone="+5511666000003", full_name="Beto Staff", status="active", role="staff"
        )
        session.add_all([admin, traveler, staff_user])
        await session.flush()

        await session.execute(
            text("INSERT INTO trip_travelers (id, wetravel_trip_uuid, user_id)"
                 " VALUES (gen_random_uuid(), :u, :uid)"),
            {"u": TRIP, "uid": traveler.id},
        )
        await session.execute(
            text("INSERT INTO trip_staff (id, wetravel_trip_uuid, user_id, function,"
                 " created_at, updated_at)"
                 " VALUES (gen_random_uuid(), :u, :uid, 'Guia', now(), now())"),
            {"u": TRIP, "uid": staff_user.id},
        )

        # Uma linha em cada trip, para provar o filtro por viagem
        for trip in (TRIP, OTHER_TRIP):
            await session.execute(
                text("INSERT INTO trip_recommendations"
                     " (id, wetravel_trip_uuid, name, category, neighborhood, address,"
                     "  sort_order, created_at, updated_at)"
                     " VALUES (gen_random_uuid(), :u, :n, 'restaurante', 'Urca', 'Rua X',"
                     "         0, now(), now())"),
                {"u": trip, "n": f"Rec {trip}"},
            )
        await session.execute(
            text("INSERT INTO trip_faqs (id, wetravel_trip_uuid, question, answer,"
                 " sort_order, created_at, updated_at)"
                 " VALUES (gen_random_uuid(), :u, 'Preciso de visto?', 'Depende.', 0,"
                 "         now(), now())"),
            {"u": TRIP},
        )
        await session.execute(
            text("INSERT INTO trip_emergency_contacts (id, wetravel_trip_uuid, name, role,"
                 " phone, sort_order, created_at, updated_at)"
                 " VALUES (gen_random_uuid(), :u, 'SAMU', 'Emergência', '192', 0,"
                 "         now(), now())"),
            {"u": TRIP},
        )
        await session.execute(
            text("INSERT INTO trip_phases (id, wetravel_trip_uuid, phase_type, title,"
                 " short_description, sort_order, is_locked_by_default, is_visible,"
                 " created_at, updated_at)"
                 " VALUES (gen_random_uuid(), :u, 'pre-trip', 'Documentos', '', 0,"
                 "         false, true, now(), now())"),
            {"u": TRIP},
        )
        await session.commit()


def _auth(client, phone: str) -> dict:
    otp = client.post("/auth/request-otp", json={"phone": phone})
    verify = client.post(
        "/auth/verify-otp", json={"phone": phone, "code": otp.json()["debug_code"]}
    )
    return {"Authorization": f"Bearer {verify.json()['access_token']}"}


def _admin(client):
    return _auth(client, "+5511666000001")


def test_sections_listing_groups_and_counts(client, session_factory):
    asyncio.run(_seed(session_factory))

    res = client.get(f"/console/trips/{TRIP}/sections", headers=_admin(client))

    assert res.status_code == 200
    sections = {s["key"]: s for s in res.json()["sections"]}

    assert sections["fases"]["count"] == 1
    assert sections["recomendacoes"]["count"] == 1
    assert sections["faq"]["count"] == 1
    assert sections["viajantes"]["count"] == 1
    assert sections["staff"]["count"] == 1
    assert sections["contatos_emergencia"]["count"] == 1
    assert sections["avisos"]["count"] == 0

    groups = [s["group"] for s in res.json()["sections"]]
    assert set(groups) == {"conteudo", "pessoas", "durante", "retorno"}


def test_section_rows_are_scoped_to_the_trip(client, session_factory):
    asyncio.run(_seed(session_factory))

    res = client.get(f"/console/trips/{TRIP}/sections/recomendacoes", headers=_admin(client))

    assert res.status_code == 200
    names = [row["name"] for row in res.json()["rows"]]
    assert names == [f"Rec {TRIP}"]


def test_unknown_section_returns_404(client, session_factory):
    asyncio.run(_seed(session_factory))

    res = client.get(f"/console/trips/{TRIP}/sections/inexistente", headers=_admin(client))

    assert res.status_code == 404


def test_fases_is_listed_but_not_served_by_the_generic_route(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    listed = {s["key"] for s in client.get(
        f"/console/trips/{TRIP}/sections", headers=headers
    ).json()["sections"]}
    assert "fases" in listed

    res = client.get(f"/console/trips/{TRIP}/sections/fases", headers=headers)
    assert res.status_code == 404


def test_travelers_section_exposes_no_sensitive_profile_data(client, session_factory):
    asyncio.run(_seed(session_factory))

    async def _add_profile():
        async with session_factory() as session:
            tt_id = await session.scalar(
                text("SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = :u"), {"u": TRIP}
            )
            await session.execute(
                text("INSERT INTO traveler_profiles (id, trip_traveler_id, passport_number,"
                     " passport_country, date_of_birth, dietary_restrictions_details,"
                     " updated_at)"
                     " VALUES (gen_random_uuid(), :tt, 'YB123456', 'BRA', '1990-05-04',"
                     "         'sem gluten', now())"),
                {"tt": tt_id},
            )
            await session.commit()

    asyncio.run(_add_profile())

    res = client.get(f"/console/trips/{TRIP}/sections/viajantes", headers=_admin(client))

    assert res.status_code == 200
    body = res.text
    for secret in ("YB123456", "1990-05-04", "sem gluten"):
        assert secret not in body, f"dado sensível vazou: {secret}"

    # Passaporte sem dados de chegada é perfil parcial, não concluído.
    row = res.json()["rows"][0]
    assert row["full_name"] == "Ana Viajante"
    assert row["profile_completed"] is False

    async def _finish_profile():
        async with session_factory() as session:
            await session.execute(
                text("UPDATE traveler_profiles SET arrival_date = '2027-07-01'")
            )
            await session.commit()

    asyncio.run(_finish_profile())

    res = client.get(f"/console/trips/{TRIP}/sections/viajantes", headers=_admin(client))
    assert res.json()["rows"][0]["profile_completed"] is True
    assert "YB123456" not in res.text


def test_sections_require_google_console_access(client, session_factory, monkeypatch):
    asyncio.run(_seed(session_factory))
    monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "false")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_CLIENT_ID", "client.apps.googleusercontent.com"
    )

    assert client.get(f"/console/trips/{TRIP}/sections").status_code == 401

    traveler = _auth(client, "+5511666000002")
    assert client.get(
        f"/console/trips/{TRIP}/sections", headers=traveler
    ).status_code == 401


def test_put_section_replaces_list_and_sets_order(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    res = client.put(
        f"/console/trips/{TRIP}/sections/faq",
        headers=headers,
        json={"items": [
            {"question": "Segunda?", "answer": "Sim."},
            {"question": "Primeira?", "answer": "Também."},
        ]},
    )

    assert res.status_code == 200
    assert res.json()["count"] == 2

    rows = client.get(f"/console/trips/{TRIP}/sections/faq", headers=headers).json()["rows"]
    assert [r["question"] for r in rows] == ["Segunda?", "Primeira?"]


def test_put_section_accepts_optional_columns_left_empty(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    res = client.put(
        f"/console/trips/{TRIP}/sections/contatos_emergencia",
        headers=headers,
        json={"items": [{"name": "Hospital", "role": "", "phone": None}]},
    )

    assert res.status_code == 200
    rows = client.get(
        f"/console/trips/{TRIP}/sections/contatos_emergencia", headers=headers
    ).json()["rows"]
    assert rows[0]["name"] == "Hospital"
    assert rows[0]["phone"] is None


def test_put_section_rejects_empty_required_field(client, session_factory):
    asyncio.run(_seed(session_factory))

    res = client.put(
        f"/console/trips/{TRIP}/sections/faq",
        headers=_admin(client),
        json={"items": [{"question": "   ", "answer": "Resposta"}]},
    )

    assert res.status_code == 422
    assert "question" in res.json()["detail"]


def test_put_section_does_not_touch_other_trips(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    async def _faq_in_other_trip():
        async with session_factory() as session:
            await session.execute(
                text("INSERT INTO trip_faqs (id, wetravel_trip_uuid, question, answer,"
                     " sort_order, created_at, updated_at)"
                     " VALUES (gen_random_uuid(), :u, 'Outra?', 'Outra.', 0, now(), now())"),
                {"u": OTHER_TRIP},
            )
            await session.commit()

    asyncio.run(_faq_in_other_trip())

    client.put(
        f"/console/trips/{TRIP}/sections/faq",
        headers=headers,
        json={"items": [{"question": "Nova?", "answer": "Nova."}]},
    )

    async def _other_still_there():
        async with session_factory() as session:
            return await session.scalar(
                text("SELECT count(*) FROM trip_faqs WHERE wetravel_trip_uuid = :u"),
                {"u": OTHER_TRIP},
            )

    assert asyncio.run(_other_still_there()) == 1


def test_put_on_a_section_without_editing_returns_405(client, session_factory):
    asyncio.run(_seed(session_factory))

    res = client.put(
        f"/console/trips/{TRIP}/sections/viajantes",
        headers=_admin(client),
        json={"items": []},
    )

    assert res.status_code == 405


def test_sections_listing_marks_which_ones_are_editable(client, session_factory):
    asyncio.run(_seed(session_factory))

    sections = {s["key"]: s for s in client.get(
        f"/console/trips/{TRIP}/sections", headers=_admin(client)
    ).json()["sections"]}

    assert sections["faq"]["editable"] is True
    assert sections["contatos_operacionais"]["editable"] is True
    assert sections["viajantes"]["editable"] is False
    assert sections["roteiro"]["editable"] is False


def _rec(**overrides) -> dict:
    return {"name": "Aprazível", "category": "restaurants", **overrides}


def test_put_recommendations_saves_rich_fields(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    res = client.put(
        f"/console/trips/{TRIP}/sections/recomendacoes",
        headers=headers,
        json={"items": [
            _rec(name="Segundo", neighborhood="Urca", rating="4.5",
                 map_url="https://maps.example.com/x", description="Vista linda"),
            _rec(name="Primeiro", neighborhood="Santa Teresa"),
        ]},
    )

    assert res.status_code == 200
    rows = client.get(
        f"/console/trips/{TRIP}/sections/recomendacoes", headers=headers
    ).json()["rows"]
    assert [r["name"] for r in rows] == ["Segundo", "Primeiro"]
    assert rows[0]["neighborhood"] == "Urca"


def test_put_recommendations_requires_name_and_category(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    sem_nome = client.put(
        f"/console/trips/{TRIP}/sections/recomendacoes",
        headers=headers, json={"items": [_rec(name="")]},
    )
    assert sem_nome.status_code == 422
    assert "name" in sem_nome.json()["detail"]

    sem_categoria = client.put(
        f"/console/trips/{TRIP}/sections/recomendacoes",
        headers=headers, json={"items": [_rec(category="")]},
    )
    assert sem_categoria.status_code == 422


def test_put_recommendations_rejects_unknown_category(client, session_factory):
    asyncio.run(_seed(session_factory))

    res = client.put(
        f"/console/trips/{TRIP}/sections/recomendacoes",
        headers=_admin(client), json={"items": [_rec(category="teleporte")]},
    )

    assert res.status_code == 422
    assert "category" in res.json()["detail"]


def test_put_recommendations_rejects_rating_out_of_range(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    for invalid in ("9", "-1", "abc"):
        res = client.put(
            f"/console/trips/{TRIP}/sections/recomendacoes",
            headers=headers, json={"items": [_rec(rating=invalid)]},
        )
        assert res.status_code == 422, f"rating {invalid} deveria ser recusado"


def test_put_recommendations_rejects_invalid_url(client, session_factory):
    asyncio.run(_seed(session_factory))

    res = client.put(
        f"/console/trips/{TRIP}/sections/recomendacoes",
        headers=_admin(client), json={"items": [_rec(map_url="ftp://x.com")]},
    )

    assert res.status_code == 422
    assert "map_url" in res.json()["detail"]


def test_put_recommendations_accepts_empty_optional_number(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    res = client.put(
        f"/console/trips/{TRIP}/sections/recomendacoes",
        headers=headers, json={"items": [_rec(rating="", map_url="")]},
    )

    assert res.status_code == 200
    rows = client.get(
        f"/console/trips/{TRIP}/sections/recomendacoes", headers=headers
    ).json()["rows"]
    assert rows[0]["rating"] is None


def test_recommendation_columns_carry_kind_and_choices(client, session_factory):
    asyncio.run(_seed(session_factory))

    columns = {c["key"]: c for c in client.get(
        f"/console/trips/{TRIP}/sections/recomendacoes", headers=_admin(client)
    ).json()["columns"]}

    assert columns["category"]["kind"] == "select"
    assert "restaurants" in columns["category"]["choices"]
    assert columns["description"]["kind"] == "textarea"
    assert columns["rating"]["kind"] == "number"
    assert columns["map_url"]["kind"] == "url"
    assert columns["photo_url"] is None if "photo_url" in columns else True


def test_legacy_category_outside_the_list_is_still_shown(client, session_factory):
    asyncio.run(_seed(session_factory))

    async def _legacy():
        async with session_factory() as session:
            await session.execute(
                text("INSERT INTO trip_recommendations (id, wetravel_trip_uuid, name,"
                     " category, sort_order, created_at, updated_at)"
                     " VALUES (gen_random_uuid(), :u, 'Legado', 'Restaurants', 9,"
                     "         now(), now())"),
                {"u": TRIP},
            )
            await session.commit()

    asyncio.run(_legacy())

    rows = client.get(
        f"/console/trips/{TRIP}/sections/recomendacoes", headers=_admin(client)
    ).json()["rows"]
    legado = [r for r in rows if r["name"] == "Legado"]
    assert legado and legado[0]["category"] == "Restaurants"


def test_trip_listing_carries_destination_travellers_and_mode(client, session_factory):
    asyncio.run(_seed(session_factory))
    headers = _admin(client)

    async def _set_mode():
        async with session_factory() as session:
            await session.execute(
                text("INSERT INTO trip_settings (id, trip_uuid, mode, created_at, updated_at)"
                     " VALUES (gen_random_uuid(), :u, 'in-trip', now(), now())"),
                {"u": TRIP},
            )
            await session.commit()

    asyncio.run(_set_mode())

    trips = {t["trip_uuid"]: t for t in client.get(
        "/console/trips", headers=headers
    ).json()["trips"]}

    trip = trips[TRIP]
    assert trip["destination"] == "Brazil"
    assert trip["traveler_count"] == 1
    assert trip["mode"] == "in-trip"

    # Viagem sem trip_settings não quebra: modo vem nulo
    assert trips[OTHER_TRIP]["mode"] is None
    assert trips[OTHER_TRIP]["traveler_count"] == 0

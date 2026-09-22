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


def test_sections_require_admin(client, session_factory):
    asyncio.run(_seed(session_factory))

    assert client.get(f"/console/trips/{TRIP}/sections").status_code == 401

    traveler = _auth(client, "+5511666000002")
    assert client.get(
        f"/console/trips/{TRIP}/sections", headers=traveler
    ).status_code == 403

"""Read-only sections of a trip, served by one generic route.

Twelve sections are plain lists. Instead of twelve near-identical routes, each one
is an entry here: a label, a group, and the SQL for its rows and its count. Section
names arriving from the client are looked up in this registry, so nothing from the
outside ever reaches SQL.

A section graduates out of here when it gains editing, as `fases` already has.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

GROUP_CONTENT = "conteudo"
GROUP_PEOPLE = "pessoas"
GROUP_DURING = "durante"
GROUP_RETURN = "retorno"

GROUP_LABELS = {
    GROUP_CONTENT: "Conteúdo do app",
    GROUP_PEOPLE: "Pessoas",
    GROUP_DURING: "Durante a viagem",
    GROUP_RETURN: "Retorno",
}


# Categorias em minúscula. O banco tem variações legadas ("Restaurants", "Beauty");
# elas continuam sendo lidas, mas só estes valores podem ser gravados.
RECOMMENDATION_CATEGORIES = (
    "restaurants", "bars", "cafes", "beaches", "landmarks", "shopping",
    "wellness", "sports", "sightseeing", "logistics", "transportation", "beauty",
)


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    required: bool = False
    # Como o editor desenha o campo: text, textarea, select, url, number.
    kind: str = "text"
    choices: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None


@dataclass(frozen=True)
class Editable:
    """How a section is written.

    Column names come from here, never from the request body: the payload is
    filtered against `columns` before any SQL is built.
    """

    table: str
    columns: tuple[str, ...]
    required: tuple[str, ...] = ()


@dataclass(frozen=True)
class Section:
    key: str
    label: str
    group: str
    count_sql: str
    rows_sql: str | None = None
    columns: tuple[Column, ...] = ()
    # Sections with their own routes are listed for the sidebar count but are not
    # served generically; the reason explains the 404 when someone asks for them.
    own_route: str | None = None
    readonly_note: str | None = None
    editable: Editable | None = None


_PHASE_COUNT = (
    "SELECT count(*) FROM trip_phases"
    " WHERE wetravel_trip_uuid = :trip_uuid AND phase_type = :phase_type"
)

SECTIONS: dict[str, Section] = {
    "fases": Section(
        key="fases",
        label="Fases pré-trip",
        group=GROUP_CONTENT,
        count_sql=_PHASE_COUNT.replace(":phase_type", "'pre-trip'"),
        own_route="/console/trips/{trip_uuid}/phases",
    ),
    "roteiro": Section(
        key="roteiro",
        columns=(Column("dia", "Dia"), Column("data", "Data"), Column("title", "Título"), Column("atividades", "Atividades"),),
        label="Roteiro",
        group=GROUP_CONTENT,
        count_sql=_PHASE_COUNT.replace(":phase_type", "'in-trip'"),
        rows_sql="""
            SELECT p.sort_order AS dia,
                   p.starts_at AS data,
                   p.title,
                   count(a.id) AS atividades
            FROM trip_phases p
            LEFT JOIN trip_activities a ON a.trip_phase_id = p.id
            WHERE p.wetravel_trip_uuid = :trip_uuid AND p.phase_type = 'in-trip'
            GROUP BY p.id, p.sort_order, p.starts_at, p.title
            ORDER BY p.sort_order
        """,
    ),
    "recomendacoes": Section(
        key="recomendacoes",
        columns=(
            Column("name", "Nome", True),
            Column("category", "Categoria", True, kind="select",
                   choices=RECOMMENDATION_CATEGORIES),
            Column("description", "Descrição", kind="textarea"),
            Column("neighborhood", "Bairro"),
            Column("location", "Cidade/Região"),
            Column("highlight", "Destaque"),
            Column("price_range", "Faixa de preço"),
            Column("address", "Endereço"),
            Column("phone", "Telefone"),
            Column("whatsapp_url", "WhatsApp", kind="url"),
            Column("map_url", "Mapa", kind="url"),
            Column("emoji", "Emoji"),
            Column("rating", "Nota", kind="number", minimum=0, maximum=5),
            Column("contact_label", "Rótulo do contato"),
        ),
        label="Recomendações",
        group=GROUP_CONTENT,
        count_sql="SELECT count(*) FROM trip_recommendations WHERE wetravel_trip_uuid = :trip_uuid",
        rows_sql="""
            SELECT name, category, description, neighborhood, location, highlight,
                   price_range, address, phone, whatsapp_url, map_url, emoji,
                   rating, contact_label
            FROM trip_recommendations
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY sort_order, name
        """,
        editable=Editable(
            "trip_recommendations",
            ("name", "category", "description", "neighborhood", "location", "highlight",
             "price_range", "address", "phone", "whatsapp_url", "map_url", "emoji",
             "rating", "contact_label"),
            ("name", "category"),
        ),
    ),
    "faq": Section(
        key="faq",
        columns=(Column("question", "Pergunta", True), Column("answer", "Resposta", True),),
        label="FAQ",
        group=GROUP_CONTENT,
        count_sql="SELECT count(*) FROM trip_faqs WHERE wetravel_trip_uuid = :trip_uuid",
        rows_sql="""
            SELECT question, answer
            FROM trip_faqs
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY sort_order
        """,
        editable=Editable("trip_faqs", ("question", "answer"), ("question", "answer")),
    ),
    "politica_cancelamento": Section(
        key="politica_cancelamento",
        columns=(Column("title", "Título", True), Column("body", "Texto", True),),
        label="Política de cancelamento",
        group=GROUP_CONTENT,
        count_sql=(
            "SELECT count(*) FROM trip_cancellation_policies"
            " WHERE wetravel_trip_uuid = :trip_uuid"
        ),
        rows_sql="""
            SELECT title, body
            FROM trip_cancellation_policies
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY sort_order
        """,
        editable=Editable(
            "trip_cancellation_policies", ("title", "body"), ("title", "body")
        ),
    ),
    "contatos_emergencia": Section(
        key="contatos_emergencia",
        columns=(Column("name", "Nome", True), Column("role", "Função"), Column("phone", "Telefone"),),
        label="Contatos de emergência",
        group=GROUP_CONTENT,
        count_sql=(
            "SELECT count(*) FROM trip_emergency_contacts"
            " WHERE wetravel_trip_uuid = :trip_uuid"
        ),
        rows_sql="""
            SELECT name, role, phone
            FROM trip_emergency_contacts
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY sort_order, name
        """,
        editable=Editable("trip_emergency_contacts", ("name", "role", "phone"), ("name",)),
    ),
    "viajantes": Section(
        key="viajantes",
        columns=(Column("full_name", "Nome"), Column("phone", "Telefone"), Column("email", "E-mail"), Column("profile_completed", "Perfil preenchido"),),
        label="Viajantes",
        group=GROUP_PEOPLE,
        count_sql="SELECT count(*) FROM trip_travelers WHERE wetravel_trip_uuid = :trip_uuid",
        # Deliberately narrow: traveler_profiles holds passport, date of birth, gender,
        # dietary and insurance data. None of it belongs on an admin screen, so the
        # profile is reduced to a boolean.
        rows_sql="""
            SELECT u.full_name,
                   u.phone,
                   u.email,
                   (pr.id IS NOT NULL
                    AND pr.passport_number IS NOT NULL
                    AND pr.arrival_date IS NOT NULL) AS profile_completed
            FROM trip_travelers tt
            JOIN users u ON u.id = tt.user_id
            LEFT JOIN traveler_profiles pr ON pr.trip_traveler_id = tt.id
            WHERE tt.wetravel_trip_uuid = :trip_uuid
            ORDER BY u.full_name NULLS LAST
        """,
        readonly_note="Viajantes vêm do WeTravel.",
    ),
    "staff": Section(
        key="staff",
        columns=(Column("full_name", "Nome"), Column("function", "Função"), Column("phone", "Telefone"),),
        label="Staff",
        group=GROUP_PEOPLE,
        count_sql="SELECT count(*) FROM trip_staff WHERE wetravel_trip_uuid = :trip_uuid",
        rows_sql="""
            SELECT u.full_name, s.function, u.phone
            FROM trip_staff s
            JOIN users u ON u.id = s.user_id
            WHERE s.wetravel_trip_uuid = :trip_uuid
            ORDER BY u.full_name NULLS LAST
        """,
    ),
    "contatos_operacionais": Section(
        key="contatos_operacionais",
        columns=(Column("category", "Categoria", True), Column("name", "Nome", True), Column("role", "Função"), Column("phone", "Telefone"),),
        label="Contatos operacionais",
        group=GROUP_PEOPLE,
        count_sql="SELECT count(*) FROM trip_contacts WHERE wetravel_trip_uuid = :trip_uuid",
        rows_sql="""
            SELECT category, name, role, phone
            FROM trip_contacts
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY category, sort_order, name
        """,
        editable=Editable(
            "trip_contacts", ("category", "name", "role", "phone"), ("category", "name")
        ),
    ),
    "avisos": Section(
        key="avisos",
        columns=(Column("title", "Título"), Column("body", "Texto"), Column("created_at", "Enviado em"),),
        label="Avisos",
        group=GROUP_DURING,
        count_sql="SELECT count(*) FROM trip_announcements WHERE wetravel_trip_uuid = :trip_uuid",
        rows_sql="""
            SELECT title, body, created_at
            FROM trip_announcements
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY created_at DESC
        """,
    ),
    "tarefas_staff": Section(
        key="tarefas_staff",
        columns=(Column("title", "Tarefa"), Column("fase", "Fase"), Column("responsavel", "Responsável"),),
        label="Tarefas de staff",
        group=GROUP_DURING,
        count_sql="""
            SELECT count(*) FROM staff_tasks s
            JOIN trip_phases p ON p.id = s.trip_phase_id
            WHERE p.wetravel_trip_uuid = :trip_uuid
        """,
        rows_sql="""
            SELECT s.title, p.title AS fase, u.full_name AS responsavel
            FROM staff_tasks s
            JOIN trip_phases p ON p.id = s.trip_phase_id
            LEFT JOIN users u ON u.id = s.assigned_to_user_id
            WHERE p.wetravel_trip_uuid = :trip_uuid
            ORDER BY p.sort_order, s.sort_order
        """,
    ),
    "feedbacks": Section(
        key="feedbacks",
        columns=(Column("viajante", "Viajante"), Column("feedback", "Feedback"), Column("created_at", "Enviado em"),),
        label="Feedbacks",
        group=GROUP_RETURN,
        count_sql="""
            SELECT count(*) FROM traveler_app_feedback f
            JOIN trip_travelers tt ON tt.id = f.trip_traveler_id
            WHERE tt.wetravel_trip_uuid = :trip_uuid
        """,
        rows_sql="""
            SELECT u.full_name AS viajante, f.feedback, f.created_at
            FROM traveler_app_feedback f
            JOIN trip_travelers tt ON tt.id = f.trip_traveler_id
            JOIN users u ON u.id = tt.user_id
            WHERE tt.wetravel_trip_uuid = :trip_uuid
            ORDER BY f.created_at DESC
        """,
        readonly_note="Escrito pelos viajantes no app.",
    ),
}


async def list_sections(session: AsyncSession, trip_uuid: str) -> dict:
    """Return every section with its group and how many rows it holds."""
    sections = []
    for section in SECTIONS.values():
        count = await session.scalar(text(section.count_sql), {"trip_uuid": trip_uuid})
        sections.append({
            "key": section.key,
            "label": section.label,
            "group": section.group,
            "group_label": GROUP_LABELS[section.group],
            "count": count or 0,
            "editable": section.own_route is not None or section.editable is not None,
            "readonly_note": section.readonly_note,
        })
    return {"sections": sections}


async def get_section_rows(session: AsyncSession, trip_uuid: str, key: str) -> dict:
    """Return the rows of one read-only section."""
    section = SECTIONS.get(key)
    if section is None:
        raise HTTPException(status_code=404, detail=f"Unknown section '{key}'")
    if section.rows_sql is None:
        raise HTTPException(
            status_code=404,
            detail=f"Section '{key}' has its own route: {section.own_route}",
        )

    result = await session.execute(text(section.rows_sql), {"trip_uuid": trip_uuid})
    rows = [dict(r._mapping) for r in result]
    return {
        "key": section.key,
        "label": section.label,
        "readonly_note": section.readonly_note,
        "editable": section.editable is not None,
        "columns": [
            {
                "key": c.key,
                "label": c.label,
                "required": c.key in (section.editable.required if section.editable else ()),
                "kind": c.kind,
                "choices": list(c.choices),
            }
            for c in section.columns
        ],
        "rows": rows,
    }


def _clean(value: object) -> str | None:
    """Trim strings; empty becomes NULL so optional columns stay empty, not blank."""
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _validate_value(column: "Column | None", value: str | None, index: int):
    """Check one value against its column kind, returning what should be stored."""
    if column is None or value is None:
        return value

    where = f"Item {index + 1}: '{column.key}'"

    if column.kind == "select" and value not in column.choices:
        allowed = ", ".join(column.choices)
        raise HTTPException(status_code=422, detail=f"{where} must be one of: {allowed}")

    if column.kind == "url" and not value.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail=f"{where} must start with http:// or https://")

    if column.kind == "number":
        try:
            number = float(value)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"{where} must be a number") from None
        if column.minimum is not None and number < column.minimum:
            raise HTTPException(
                status_code=422, detail=f"{where} must be at least {column.minimum}"
            )
        if column.maximum is not None and number > column.maximum:
            raise HTTPException(
                status_code=422, detail=f"{where} must be at most {column.maximum}"
            )
        return number

    return value


async def replace_section(
    session: AsyncSession, trip_uuid: str, key: str, items: list[dict]
) -> dict:
    """Replace every row of an editable section; list position becomes sort_order.

    Runs in a single transaction: a rejected item leaves the section untouched.
    """
    section = SECTIONS.get(key)
    if section is None:
        raise HTTPException(status_code=404, detail=f"Unknown section '{key}'")
    if section.editable is None:
        raise HTTPException(
            status_code=405,
            detail=f"Section '{section.label}' cannot be edited yet",
        )

    spec = section.editable
    by_key = {c.key: c for c in section.columns}

    # Validate everything before writing anything: a rejected item leaves the
    # section exactly as it was.
    cleaned: list[dict] = []
    for index, item in enumerate(items):
        row: dict = {column: _clean(item.get(column)) for column in spec.columns}
        for column in spec.required:
            if row[column] is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Item {index + 1}: '{column}' is required",
                )
        for key, value in list(row.items()):
            row[key] = _validate_value(by_key.get(key), value, index)
        cleaned.append(row)

    columns = ", ".join(spec.columns)
    placeholders = ", ".join(f":{column}" for column in spec.columns)

    await session.execute(
        text(f"DELETE FROM {spec.table} WHERE wetravel_trip_uuid = :trip_uuid"),
        {"trip_uuid": trip_uuid},
    )
    for index, row in enumerate(cleaned):
        await session.execute(
            text(
                f"INSERT INTO {spec.table}"
                f" (id, wetravel_trip_uuid, {columns}, sort_order, created_at, updated_at)"
                f" VALUES (gen_random_uuid(), :trip_uuid, {placeholders}, :sort_order,"
                f"         now(), now())"
            ),
            {"trip_uuid": trip_uuid, "sort_order": index, **row},
        )

    await session.commit()
    return {"key": key, "count": len(cleaned)}

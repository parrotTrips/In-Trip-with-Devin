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


@dataclass(frozen=True)
class Section:
    key: str
    label: str
    group: str
    count_sql: str
    rows_sql: str | None = None
    # Sections with their own routes are listed for the sidebar count but are not
    # served generically; the reason explains the 404 when someone asks for them.
    own_route: str | None = None
    readonly_note: str | None = None


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
        label="Recomendações",
        group=GROUP_CONTENT,
        count_sql="SELECT count(*) FROM trip_recommendations WHERE wetravel_trip_uuid = :trip_uuid",
        rows_sql="""
            SELECT name, category, neighborhood, address
            FROM trip_recommendations
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY sort_order, name
        """,
    ),
    "faq": Section(
        key="faq",
        label="FAQ",
        group=GROUP_CONTENT,
        count_sql="SELECT count(*) FROM trip_faqs WHERE wetravel_trip_uuid = :trip_uuid",
        rows_sql="""
            SELECT question, answer
            FROM trip_faqs
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY sort_order
        """,
    ),
    "politica_cancelamento": Section(
        key="politica_cancelamento",
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
    ),
    "contatos_emergencia": Section(
        key="contatos_emergencia",
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
    ),
    "viajantes": Section(
        key="viajantes",
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
        label="Contatos operacionais",
        group=GROUP_PEOPLE,
        count_sql="SELECT count(*) FROM trip_contacts WHERE wetravel_trip_uuid = :trip_uuid",
        rows_sql="""
            SELECT category, name, role, phone
            FROM trip_contacts
            WHERE wetravel_trip_uuid = :trip_uuid
            ORDER BY category, sort_order, name
        """,
    ),
    "avisos": Section(
        key="avisos",
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
            "editable": section.own_route is not None,
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
        "rows": rows,
    }

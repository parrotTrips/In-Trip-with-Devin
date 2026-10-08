"""Idempotent provisioning of the default Trip Wrap-up."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.console_service import WRAP_UP_CHECKLIST, WRAP_UP_LINKS, WRAP_UP_TEMPLATE


async def ensure_trip_wrap_ups(session: AsyncSession) -> int:
    """Create and publish the default Wrap-up for every trip that lacks one."""
    trip_uuids = (await session.execute(text("""
        SELECT w.trip_uuid
        FROM wetravel_trips w
        WHERE NOT EXISTS (
            SELECT 1 FROM trip_phases p
            WHERE p.wetravel_trip_uuid = w.trip_uuid
              AND p.phase_type = 'post-trip'
        )
        ORDER BY w.trip_uuid
    """))).scalars().all()

    for trip_uuid in trip_uuids:
        phase_id = await session.scalar(text("""
            INSERT INTO trip_phases
                (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                 short_description, detailed_description, sort_order,
                 is_locked_by_default, is_visible, created_at, updated_at)
            VALUES
                (gen_random_uuid(), :trip_uuid, 'post-trip', :title, :subtitle, :icon,
                 :short_description, :detailed_description, 0,
                 false, false, now(), now())
            RETURNING id
        """), {"trip_uuid": trip_uuid, **WRAP_UP_TEMPLATE})

        for sort_order, label in enumerate(WRAP_UP_CHECKLIST):
            await session.execute(text("""
                INSERT INTO trip_phase_checklist_items
                    (id, trip_phase_id, label, sort_order, is_required, created_at, updated_at)
                VALUES (gen_random_uuid(), :phase_id, :label, :sort_order, false, now(), now())
            """), {"phase_id": phase_id, "label": label, "sort_order": sort_order})

        for sort_order, (label, url) in enumerate(WRAP_UP_LINKS):
            await session.execute(text("""
                INSERT INTO trip_phase_links
                    (id, trip_phase_id, label, url, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), :phase_id, :label, :url, :sort_order, now(), now())
            """), {
                "phase_id": phase_id,
                "label": label,
                "url": url,
                "sort_order": sort_order,
            })

        await session.execute(
            text("UPDATE trip_phases SET is_visible = true, updated_at = now() WHERE id = :id"),
            {"id": phase_id},
        )

    await session.commit()
    return len(trip_uuids)

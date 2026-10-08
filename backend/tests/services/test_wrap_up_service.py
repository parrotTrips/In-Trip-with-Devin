import asyncio

from sqlalchemy import text

from app.services.wrap_up_service import ensure_trip_wrap_ups


def test_creates_published_wrap_up_once_for_every_missing_trip(session_factory):
    async def run():
        async with session_factory() as session:
            await session.execute(text("""
                INSERT INTO wetravel_trips (trip_uuid, title, destination)
                VALUES ('wrap-new', 'New', 'Brazil'), ('wrap-existing', 'Existing', 'Brazil')
            """))
            await session.execute(text("""
                INSERT INTO trip_phases
                    (id, wetravel_trip_uuid, phase_type, title, short_description,
                     sort_order, is_locked_by_default, is_visible, created_at, updated_at)
                VALUES (gen_random_uuid(), 'wrap-existing', 'post-trip', 'Custom', 'Keep me',
                        0, false, true, now(), now())
            """))
            await session.commit()

            assert await ensure_trip_wrap_ups(session) == 1
            assert await ensure_trip_wrap_ups(session) == 0

            rows = (await session.execute(text("""
                SELECT wetravel_trip_uuid, title, is_visible
                FROM trip_phases
                WHERE wetravel_trip_uuid IN ('wrap-new', 'wrap-existing')
                  AND phase_type = 'post-trip'
                ORDER BY wetravel_trip_uuid
            """))).all()
            assert [(r.wetravel_trip_uuid, r.title, r.is_visible) for r in rows] == [
                ('wrap-existing', 'Custom', True),
                ('wrap-new', 'Trip Wrap-up', True),
            ]
            child_counts = (await session.execute(text("""
                SELECT
                    (SELECT count(*) FROM trip_phase_checklist_items i
                     JOIN trip_phases p ON p.id = i.trip_phase_id
                     WHERE p.wetravel_trip_uuid = 'wrap-new') AS checklist_count,
                    (SELECT count(*) FROM trip_phase_links l
                     JOIN trip_phases p ON p.id = l.trip_phase_id
                     WHERE p.wetravel_trip_uuid = 'wrap-new') AS link_count
            """))).one()
            assert child_counts.checklist_count == 5
            assert child_counts.link_count == 1

    asyncio.run(run())

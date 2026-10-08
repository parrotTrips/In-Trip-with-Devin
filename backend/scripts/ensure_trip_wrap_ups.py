#!/usr/bin/env python3
"""Create the published default Wrap-up for trips that do not have one."""

import asyncio
import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.services.wrap_up_service import ensure_trip_wrap_ups


async def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(database_url)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            created = await ensure_trip_wrap_ups(session)
        print(f"Created and published {created} Trip Wrap-up phase(s).")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

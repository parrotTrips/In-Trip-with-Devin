import asyncio

from sqlalchemy import select

from app.db.models.user import User
from app.services.user_service import get_user, update_user


def test_get_user_returns_user_data(session_factory):
    async def run_test():
        async with session_factory() as session:
            user = User(
                phone="+5511777777777",
                full_name="Alice",
                status="active",
            )
            session.add(user)
            await session.commit()

            response = await get_user(str(user.id), session)

            assert response == {
                "id": str(user.id),
                "phone": "+5511777777777",
                "name": "Alice",
            }

    asyncio.run(run_test())


def test_update_user_persists_name_changes(session_factory):
    async def run_test():
        async with session_factory() as session:
            user = User(
                phone="+5511777777777",
                full_name=None,
                status="active",
            )
            session.add(user)
            await session.commit()

            response = await update_user(str(user.id), {"name": "Bob"}, session)
            refreshed_user = await session.scalar(select(User).where(User.id == user.id))
            updated_user = await get_user(str(user.id), session)

            assert response == {"message": "User updated"}
            assert refreshed_user is not None
            assert refreshed_user.full_name == "Bob"
            assert updated_user == {
                "id": str(user.id),
                "phone": "+5511777777777",
                "name": "Bob",
            }

    asyncio.run(run_test())

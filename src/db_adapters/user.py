from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_tables.user import User
from src.db_tables.user_list import UserList, UserListKind


async def user_get(session: AsyncSession, discord_id: int) -> User | None:
    """Get a user by their Discord ID."""
    return await session.get(User, discord_id)


async def user_get_safe(session: AsyncSession, discord_id: int) -> User:
    """Get a user by their Discord ID, creating them if they don't exist."""
    user = await user_get(session, discord_id)
    if user is None:
        user = User(discord_id=discord_id)
        session.add(user)
        await session.commit()

    return user


async def user_create_list(session: AsyncSession, user: User, name: str, item_kind: UserListKind) -> UserList:
    """Create a new list for a user.

    :raises ValueError: If a list with the same name already exists for the user.
    """
    if await session.get(UserList, (user.discord_id, name)) is not None:
        raise ValueError(f"List with name {name} already exists for user {user.discord_id}.")
    user_list = UserList(user_id=user.discord_id, name=name, item_kind=item_kind)
    session.add(user_list)
    await session.commit()
    await session.refresh(user, ["lists"])

    return user_list


async def user_get_list(session: AsyncSession, user: User, name: str) -> UserList | None:
    """Get a user's list by name."""
    # use where clause on user.id and name
    user_list = await session.execute(
        select(UserList)
        .where(
            UserList.user_id == user.discord_id,
        )
        .where(UserList.name == name)
    )
    return user_list.scalars().first()


async def user_get_list_safe(
    session: AsyncSession, user: User, name: str, kind: UserListKind = UserListKind.MEDIA
) -> UserList:
    """Get a user's list by name, creating it if it doesn't exist.

    :param kind: The kind of list to create if it doesn't exist.
    :return: The user list.
    """
    user_list = await user_get_list(session, user, name)
    if user_list is None:
        user_list = await user_create_list(session, user, name, kind)

    return user_list

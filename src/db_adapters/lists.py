from typing import Literal, overload

from sqlalchemy.ext.asyncio import AsyncSession

from src.db_adapters.media import ensure_media
from src.db_tables.user_list import UserList, UserListItem, UserListItemKind


@overload
async def list_put_item(
    session: AsyncSession,
    user_list: UserList,
    tvdb_id: int,
    kind: Literal[UserListItemKind.MOVIE, UserListItemKind.SERIES],
) -> UserListItem: ...


@overload
async def list_put_item(
    session: AsyncSession,
    user_list: UserList,
    tvdb_id: int,
    kind: Literal[UserListItemKind.EPISODE],
    series_id: int,
) -> UserListItem: ...


async def list_put_item(
    session: AsyncSession, user_list: UserList, tvdb_id: int, kind: UserListItemKind, series_id: int | None = None
) -> UserListItem:
    """Add an item to a user list.

    :raises ValueError: If the item is already present in the list.
    """
    if series_id:
        await ensure_media(session, tvdb_id, kind, series_id=series_id)
    else:
        await ensure_media(session, tvdb_id, kind)
    if await session.get(UserListItem, (user_list.id, tvdb_id, kind)) is not None:
        raise ValueError(f"Item {tvdb_id} is already in list {user_list.id}.")

    item = UserListItem(list_id=user_list.id, tvdb_id=tvdb_id, kind=kind)
    session.add(item)
    await session.commit()
    return item


async def list_get_item(
    session: AsyncSession, user_list: UserList, tvdb_id: int, kind: UserListItemKind
) -> UserListItem | None:
    """Get an item from a user list."""
    return await session.get(UserListItem, (user_list.id, tvdb_id, kind))


async def list_remove_item(session: AsyncSession, user_list: UserList, item: UserListItem) -> None:
    """Remove an item from a user list."""
    await session.delete(item)
    await session.commit()
    await session.refresh(user_list, ["items"])


async def list_remove_item_safe(
    session: AsyncSession, user_list: UserList, tvdb_id: int, kind: UserListItemKind
) -> None:
    """Removes an item from a user list if it exists."""
    if item := await list_get_item(session, user_list, tvdb_id, kind):
        await list_remove_item(session, user_list, item)


async def list_put_item_safe(
    session: AsyncSession, user_list: UserList, tvdb_id: int, kind: UserListItemKind, series_id: int | None = None
) -> UserListItem:
    """Add an item to a user list, or return the existing item if it is already present."""
    await ensure_media(session, tvdb_id, kind, series_id=series_id)
    item = await list_get_item(session, user_list, tvdb_id, kind)
    if item:
        return item

    item = UserListItem(list_id=user_list.id, tvdb_id=tvdb_id, kind=kind)
    session.add(item)
    await session.commit()
    return item


async def refresh_list_items(session: AsyncSession, user_list: UserList) -> None:
    """Refresh the items in a user list."""
    await session.refresh(user_list, ["items"])


async def get_list_item(
    session: AsyncSession,
    user_list: UserList,
    tvdb_id: int,
    kind: UserListItemKind,
) -> UserListItem | None:
    """Get a user list."""
    return await session.get(UserListItem, (user_list.id, tvdb_id, kind))

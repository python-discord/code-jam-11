from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.db_tables.media import Episode, Movie, Series
from src.db_tables.user_list import UserListItemKind


async def ensure_media(session: AsyncSession, tvdb_id: int, kind: UserListItemKind, **kwargs: Any) -> None:
    """Ensure that a tvdb media item is present in its respective table."""
    match kind:
        case UserListItemKind.MOVIE:
            cls = Movie
        case UserListItemKind.SERIES:
            cls = Series
        case UserListItemKind.EPISODE:
            cls = Episode
    media = await session.get(cls, tvdb_id)
    if media is None:
        media = cls(tvdb_id=tvdb_id, **kwargs)
        session.add(media)
        await session.commit()

    if isinstance(media, Episode):
        await session.refresh(media, ["series"])
        if not media.series:
            series = Series(tvdb_id=kwargs["series_id"])
            session.add(series)
            await session.commit()

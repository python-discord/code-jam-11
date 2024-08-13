from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import cached_property
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Database wrapper."""

    def __init__(self, url: str, **kw: dict[str, Any]) -> None:
        self.engine = create_async_engine(
            url,
            pool_pre_ping=True,
            echo=kw.pop("echo", False),
        )

    @cached_property
    def session_maker(self) -> async_sessionmaker[AsyncSession]:
        """Cached session maker."""
        return async_sessionmaker(
            self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def create_session(self) -> AsyncIterator[AsyncSession]:
        """Create a session context manager."""
        async with self.session_maker() as async_session:
            try:
                yield async_session
            except Exception:
                await async_session.rollback()
                raise
            finally:
                await async_session.close()


# TODO: move this to a container
database = Database("sqlite+aiosqlite:///./test.db")
trivia_database = Database("sqlite+aiosqlite:///./trivia.db")

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Result, select
from sqlalchemy.sql.functions import count

from app.models.guess import Guess

from .database import Database, database


class GuessRepo:
    """Repository for interacting with Guess."""

    def __init__(self, db: Database) -> None:
        self.db: Database = db

    async def create(
        self,
        content: str,
        result: str,
        wordle_id: UUID,
    ) -> Guess:
        """Create a guess."""
        async with self.db.create_session() as session:
            guess = Guess(content=content, result=result, wordle_id=wordle_id)
            session.add(guess)
            await session.commit()
            await session.refresh(guess)
            return guess

    async def get(self, id: UUID) -> Guess | None:
        """Get guess by id."""
        async with self.db.create_session() as session:
            stmt = select(Guess).where(Guess.id == id)
            result = await session.execute(stmt)
            guess: Guess | None = result.scalar()
            return guess

    async def get_by_wordle_id(self, wordle_id: UUID) -> Sequence[Guess]:
        """Get all guesses by wordle ID."""
        async with self.db.create_session() as session:
            stmt = select(Guess).where(Guess.wordle_id == wordle_id)
            result: Result[Any] = await session.execute(stmt)
            guesses: Sequence[Guess] = result.scalars().all()
            return guesses

    async def count_by_wordle_ids(self, wordle_ids: Sequence[UUID]) -> int:
        """Count number of guesses by all wordle IDs."""
        async with self.db.create_session() as session:
            stmt = (
                select(count())
                .select_from(Guess)
                .where(Guess.wordle_id.in_(wordle_ids))
            )
            result: Result[Any] = await session.execute(stmt)
            cnt: int = result.scalar()
            return cnt


# TODO: move this to a container
guess_repo = GuessRepo(database)

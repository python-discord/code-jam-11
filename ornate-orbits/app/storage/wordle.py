import logging
from collections.abc import Sequence
from typing import Any, Final
from uuid import UUID

from sqlalchemy import Result, desc, select, update

from app.enums import MatchResult
from app.models.guess import Guess
from app.models.wordle import Wordle, WordleStatus

from .database import Database, database

logger = logging.getLogger(__name__)


class WordleNotFoundError(Exception):
    """Wordle not found error."""


class WordleRepo:
    """Repository for interacting with Wordle."""

    TRIVIA_THRESHOLD: Final[int] = 3

    def __init__(self, db: Database) -> None:
        self.db: Database = db

    async def create(
        self,
        word: str,
        user_id: int,
    ) -> Wordle:
        """Create a wordle."""
        async with self.db.create_session() as session:
            wordle = Wordle(
                word=word, user_id=user_id, status=WordleStatus.ACTIVE.value
            )
            session.add(wordle)
            await session.commit()
            await session.refresh(wordle)
            return wordle

    async def get(self, id: UUID) -> Wordle | None:
        """Get wordle by id."""
        async with self.db.create_session() as session:
            stmt = select(Wordle).where(Wordle.id == id)
            result = await session.execute(stmt)
            wordle: Wordle | None = result.scalar()
            return wordle

    async def get_by_user_id(self, user_id: int) -> Sequence[Wordle]:
        """Get wordle by user id."""
        async with self.db.create_session() as session:
            stmt = (
                select(Wordle)
                .where(Wordle.user_id == user_id)
                .order_by(desc(Wordle.created_at))
            )
            result: Result[Any] = await session.execute(stmt)
            wordles: Sequence[Wordle] = result.scalars().all()
            return wordles

    async def get_active_wordle_by_user_id(
        self,
        user_id: int,
    ) -> Wordle | None:
        """Get the active wordle by user id."""
        async with self.db.create_session() as session:
            stmt = select(Wordle).where(
                Wordle.user_id == user_id,
                Wordle.status == WordleStatus.ACTIVE.value,
            )

            result = await session.execute(stmt)
            wordle: Wordle | None = result.scalar()
            return wordle

    async def get_pending_wordle(self, user_id: int) -> Wordle | None:
        """Get the pending wordle by user id."""
        async with self.db.create_session() as session:
            stmt = select(Wordle).where(
                Wordle.user_id == user_id,
                Wordle.status == WordleStatus.PENDING.value,
            )
            result = await session.execute(stmt)
            wordle: Wordle | None = result.scalar()
            return wordle

    async def get_ongoing_wordle(self, user_id: int) -> Wordle | None:
        """Get unfinished wordle game by user id."""
        async with self.db.create_session() as session:
            stmt = select(Wordle).where(
                Wordle.user_id == user_id,
                Wordle.status.in_(
                    [
                        WordleStatus.ACTIVE.value,
                        WordleStatus.PENDING.value,
                    ]
                ),
            )
            result = await session.execute(stmt)
            wordle: Wordle | None = result.scalar()
            return wordle

    async def _calculate_next_status(self, id: UUID) -> WordleStatus | None:
        wordle = await wordle_repo.get(id=id)
        if wordle is None:
            return None
        match wordle.status:
            case WordleStatus.ACTIVE.value:
                guesses = await wordle_repo.get_guesses(wordle.user_id)
                if len(guesses) < self.TRIVIA_THRESHOLD:
                    return None
                recent_results = [
                    guess.result for guess in guesses[-self.TRIVIA_THRESHOLD :]
                ]
                if str(
                    MatchResult.CORRECT_LETTER_CORRECT_POSITION
                ) not in "".join(recent_results):
                    return WordleStatus.PENDING.value
                return None
            case WordleStatus.PENDING.value:
                return WordleStatus.ACTIVE.value
            case WordleStatus.COMPLETED.value:
                return None
            case _:
                raise ValueError

    async def change_status(
        self,
        id: UUID,
        *,
        is_winning: bool = False,
        is_ending: bool = False,
    ) -> None:
        """Change the wordle status based on the current guess."""
        if is_winning and not is_ending:
            next_status = WordleStatus.COMPLETED.value
        elif is_ending and not is_winning:
            next_status = WordleStatus.ABORTED.value
        else:
            next_status = await self._calculate_next_status(id)
        if next_status is None:
            return
        logger.info("next status = %s", next_status)
        async with self.db.create_session() as session:
            stmt = (
                update(Wordle)
                .where(Wordle.id == id)
                .values(status=next_status)
            )
            await session.execute(stmt)
            await session.commit()

    async def win_game(self, id: UUID) -> None:
        """Change the status when the play wins."""

    async def get_guesses(self, user_id: int) -> Sequence[Guess]:
        """Get the guesses of the active wordle of a user."""
        async with self.db.create_session() as session:
            stmt = select(Wordle).where(
                Wordle.user_id == user_id,
                Wordle.status == WordleStatus.ACTIVE.value,
            )
            result = await session.execute(stmt)
            wordle: Wordle | None = result.scalar()
            if wordle is None:
                raise WordleNotFoundError
            return wordle.guesses


# TODO: move this to a container
wordle_repo = WordleRepo(database)

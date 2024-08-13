from sqlalchemy import func, select

from app.models.trivia import Trivia

from .database import Database, trivia_database


class TriviaRepo:
    """Repository for interacting with Trivia."""

    def __init__(self, db: Database) -> None:
        self.db: Database = db

    async def create(
        self,
        trivia: Trivia,
    ) -> Trivia:
        """Create a trivia."""
        async with self.db.create_session() as session:
            session.add(trivia)
            await session.commit()
            await session.refresh(trivia)
            return trivia

    async def get_random(self) -> Trivia:
        """Get a random trivia question."""
        async with self.db.create_session() as session:
            stmt = select(Trivia).order_by(func.random())
            result = await session.execute(stmt)
            trivia: Trivia | None = result.scalar()
            assert trivia, "no trivia in the database"
            return trivia


# TODO: move this to a container
trivia_repo = TriviaRepo(trivia_database)

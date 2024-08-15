import asyncio
import logging

from .bot import bot
from .models.base import Base
from .settings import settings
from .storage.database import database
from .word_generator import WordGenerator


async def init_db() -> None:
    """Seeds the tables."""
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main() -> None:
    """Run the app."""
    logging.basicConfig(level=logging.INFO)
    # TODO: move this to bot start hook
    WordGenerator.download_corpus()
    WordGenerator.boot()

    asyncio.run(init_db())
    bot.run(settings.DISCORD_TOKEN)


if __name__ == "__main__":
    main()

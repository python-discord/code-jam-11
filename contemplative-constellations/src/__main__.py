import asyncio

import aiohttp
import discord
from aiocache import SimpleMemoryCache

from src.bot import Bot
from src.settings import BOT_TOKEN, SQLITE_DATABASE_FILE
from src.utils.database import apply_db_migrations, engine, get_db_session, load_db_models
from src.utils.log import get_logger

log = get_logger(__name__)


async def _init_database(*, retries: int = 5, retry_time: float = 3) -> None:
    """Try to connect to the database, keep trying if we fail.

    :param retries: Number of re-try attempts, in case db connection fails.
    :param retry_time: Time to wait between re-try attempts.
    """
    load_db_models()

    # NOTE: The retry logic here isn't that useful with sqlite databases, but it's here
    # in case we switch to a different database in the future.
    for _ in range(retries):
        log.debug(f"Connecting to the database: {SQLITE_DATABASE_FILE}")
        try:
            conn = engine.connect()
        except ConnectionRefusedError as exc:
            log.exception(f"Database connection failed, retrying in {retry_time} seconds.", exc_info=exc)
            await asyncio.sleep(retry_time)
        else:
            async with conn, conn.begin():
                await conn.run_sync(apply_db_migrations)
            break

    log.debug("Database connection established")


async def main() -> None:
    """Main entrypoint of the application.

    This will load all of the extensions and start the bot.
    """
    intents = discord.Intents().default()
    intents.message_content = True

    await _init_database()

    cache = SimpleMemoryCache()

    async with aiohttp.ClientSession() as http_session, get_db_session() as db_session:
        bot = Bot(intents=intents, http_session=http_session, db_session=db_session, cache=cache)
        bot.load_all_extensions()

        log.info("Starting the bot...")
        async with bot as bot_:
            await bot_.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

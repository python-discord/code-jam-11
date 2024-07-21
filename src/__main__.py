import asyncio

import aiohttp
import discord

from src.bot import Bot
from src.settings import BOT_TOKEN
from src.utils.log import get_logger

log = get_logger(__name__)


async def main() -> None:
    """Main entrypoint of the application.

    This will load all of the extensions and start the bot.
    """
    intents = discord.Intents().default()
    intents.message_content = True

    async with aiohttp.ClientSession() as http_session:
        bot = Bot(intents=intents, http_session=http_session)
        bot.load_all_extensions()

        log.info("Starting the bot...")
        async with bot as bot_:
            await bot_.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

import discord

from src.settings import BOT_TOKEN
from src.utils.log import get_logger

log = get_logger(__name__)

EXTENSIONS = [
    "src.exts.ping",
    "src.exts.error_handler",
]

intents = discord.Intents().default()
intents.message_content = True
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready() -> None:
    """Function called once the bot is ready and online."""
    log.info(f"{bot.user} is ready and online!")


async def main() -> None:
    """Main entrypoint of the application.

    This will load all of the extensions and start the bot.
    """
    log.info("Loading extensions...")
    bot.load_extensions(*EXTENSIONS)

    log.info("Starting the bot...")
    async with bot:
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

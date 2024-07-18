import discord

from src.settings import BOT_TOKEN
from src.utils.log import get_logger

log = get_logger(__name__)

bot = discord.Bot()


@bot.event
async def on_ready() -> None:
    """Function called once the bot is ready and online."""
    log.info(f"{bot.user} is ready and online!")


@bot.slash_command()
async def ping(ctx: discord.ApplicationContext) -> None:
    """Test out bot's latency."""
    _ = await ctx.respond(f"Pong! ({(bot.latency * 1000):.2f}ms)")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)

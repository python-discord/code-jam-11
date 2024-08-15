from discord import ApplicationContext, Cog, slash_command

from src.bot import Bot
from src.utils.log import get_logger

log = get_logger(__name__)


class PingCog(Cog):
    """Cog to verify the bot is working."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command()
    async def ping(self, ctx: ApplicationContext) -> None:
        """Test out bot's latency."""
        await ctx.respond(f"Pong! ({(self.bot.latency * 1000):.2f}ms)")


def setup(bot: Bot) -> None:
    """Register the PingCog cog."""
    bot.add_cog(PingCog(bot))

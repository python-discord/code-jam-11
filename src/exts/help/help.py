import aiohttp
from discord import ApplicationContext, Bot, Cog, Embed, slash_command

from src.utils import mention_command
from src.utils.log import get_logger

log = get_logger(__name__)
CAT_URL: str = "https://api.thecatapi.com/v1/images/search"


class HelpCog(Cog):
    """Cog to verify the bot is working."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command()
    async def help(self, ctx: ApplicationContext) -> None:
        """Help command shows available commands."""
        async with aiohttp.ClientSession().get(CAT_URL) as response:
            response.raise_for_status()
            data = await response.json()
            url: str = data[0]["url"]

        embed = Embed(
            title="Help command",
            image=url,
        )
        embed.add_field(name=mention_command("ping", self.bot), value="sends a response with pong", inline=False)
        embed.add_field(name=mention_command("help", self.bot), value="gives a list of available commands for users")
        embed.add_field(name="", value="")
        await ctx.respond(embed=embed)


def setup(bot: Bot) -> None:
    """Register the HelpCog cog."""
    bot.add_cog(HelpCog(bot))

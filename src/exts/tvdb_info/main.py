from typing import Literal

import aiohttp
import discord
from discord import ApplicationContext, Cog, option, slash_command

from src.bot import Bot
from src.tvdb import TvdbClient
from src.tvdb.models import SearchResults
from src.utils.log import get_logger

log = get_logger(__name__)


class InfoView(discord.ui.View):
    """View for displaying information about a movie or series."""

    def __init__(self, results: SearchResults):
        super().__init__(disable_on_timeout=True)
        self.results: SearchResults = results
        self.dropdown = discord.ui.Select(
            placeholder="Not what you're looking for? Select a different result.",
            options=[
                discord.SelectOption(
                    label=result.name or result.title or "",
                    value=str(i),
                    description=result.overview[:100] if result.overview else None,
                )
                for i, result in enumerate(self.results)
            ],
        )
        self.dropdown.callback = self._dropdown_callback
        self.add_item(self.dropdown)
        self.index = 0

    def _get_embed(self) -> discord.Embed:
        result = self.results[self.index]
        embed = discord.Embed(
            title=result.name or result.title, description=result.overview or "No overview available."
        )
        embed.set_image(url=result.image_url)
        return embed

    async def _dropdown_callback(self, interaction: discord.Interaction) -> None:
        if not self.dropdown.values or not isinstance(self.dropdown.values[0], str):
            log.error("Dropdown values are empty or not a string but callback was triggered.")
            return
        self.index = int(self.dropdown.values[0])
        if not self.message:
            log.error("Message is not set but callback was triggered.")
            return
        await self.message.edit(embed=self._get_embed(), view=self)
        await interaction.response.defer()

    async def send(self, ctx: ApplicationContext) -> None:
        """Send the view."""
        await ctx.respond(embed=self._get_embed(), view=self)


class InfoCog(Cog):
    """Cog to verify the bot is working."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command()
    @option("query", input_type=str, description="The query to search for.")
    @option(
        "type",
        input_type=str,
        parameter_name="entity_type",
        description="The type of entity to search for.",
        choices=["movie", "series"],
    )
    async def search(self, ctx: ApplicationContext, query: str, entity_type: Literal["movie", "series"]) -> None:
        """Test out bot's latency."""
        async with aiohttp.ClientSession() as session:
            client = TvdbClient(session)
            match entity_type:
                case "movie":
                    response = await client.movies.search(query, limit=5)
                case "series":
                    response = await client.series.search(query, limit=5)

        if not response:
            await ctx.respond("No results found.")
            return
        view = InfoView(response)
        await view.send(ctx)


def setup(bot: Bot) -> None:
    """Register the PingCog cog."""
    bot.add_cog(InfoCog(bot))

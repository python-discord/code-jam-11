from typing import Literal

import aiohttp
import discord
from discord import ApplicationContext, Cog, option, slash_command

from src.bot import Bot
from src.settings import THETVDB_COPYRIGHT_FOOTER, THETVDB_LOGO
from src.tvdb import TvdbClient
from src.tvdb.models import SearchResults
from src.utils.log import get_logger

log = get_logger(__name__)

MOVIE_EMOJI = "🎬"
SERIES_EMOJI = "📺"


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
        original_title = result.name
        en_title = result.translations["eng"]
        original_overview = result.overview
        en_overview = result.overviews["eng"]
        if en_overview and en_overview != original_overview:
            overview = f"{en_overview}"
        elif not en_overview and original_overview:
            overview = f"{original_overview}\n\n*No English overview available.*"
        else:
            overview = "*No overview available.*"
        if original_title and original_title != en_title:
            title = f"{original_title} ({en_title})"
        else:
            title = en_title
        if result.id[0] == "m":
            title = f"{MOVIE_EMOJI} {title}"
            url = f"https://www.thetvdb.com/movies/{result.slug}"
        else:
            title = f"{SERIES_EMOJI} {title}"
            url = f"https://www.thetvdb.com/series/{result.slug}"
        embed = discord.Embed(title=title, color=discord.Color.blurple(), url=url)
        embed.add_field(name="Overview", value=overview, inline=False)
        embed.set_footer(text=THETVDB_COPYRIGHT_FOOTER, icon_url=THETVDB_LOGO)
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

    @slash_command(
        name="search",
        description="Search for a movie or series.",
    )
    @option("query", input_type=str, description="The query to search for.")
    @option(
        "type",
        input_type=str,
        parameter_name="entity_type",
        description="The type of entity to search for.",
        choices=["movie", "series"],
        required=False,
    )
    async def search(
        self, ctx: ApplicationContext, query: str, entity_type: Literal["movie", "series"] | None = None
    ) -> None:
        """Search for a movie or series."""
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            client = TvdbClient(session)
            match entity_type:
                case "movie":
                    response = await client.movies.search(query, limit=5)
                case "series":
                    response = await client.series.search(query, limit=5)
                case None:
                    response = await client.search(query, limit=5)

        if not response:
            await ctx.respond("No results found.")
            return
        view = InfoView(response)
        await view.send(ctx)


def setup(bot: Bot) -> None:
    """Register the PingCog cog."""
    bot.add_cog(InfoCog(bot))

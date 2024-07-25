from collections.abc import Sequence
from typing import Literal

import aiohttp
import discord
from discord import ApplicationContext, Cog, option, slash_command

from src.bot import Bot
from src.settings import THETVDB_COPYRIGHT_FOOTER, THETVDB_LOGO
from src.tvdb import FetchMeta, Movie, Series, TvdbClient
from src.tvdb.errors import InvalidIdError
from src.utils.log import get_logger

log = get_logger(__name__)

MOVIE_EMOJI = "🎬"
SERIES_EMOJI = "📺"


class InfoView(discord.ui.View):
    """View for displaying information about a movie or series."""

    def __init__(self, results: Sequence[Movie | Series]) -> None:
        super().__init__(disable_on_timeout=True)
        self.results = results
        if len(self.results) > 1:
            self.dropdown = discord.ui.Select(
                placeholder="Not what you're looking for? Select a different result.",
                options=[
                    discord.SelectOption(
                        label=(result.bilingual_name or "")[:100],
                        value=str(i),
                        description=result.overview[:100] if result.overview else None,
                    )
                    for i, result in enumerate(self.results)
                ],
            )
            self.dropdown.callback = self._dropdown_callback
            self.add_item(self.dropdown)
            self.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.success,
                    label="Mark as watched",
                    emoji="✅",
                    disabled=True,
                    row=1,
                )
            )
            self.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="Favorite",
                    emoji="⭐",
                    disabled=True,
                    row=1,
                )
            )
            self.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="View episodes",
                    emoji="📺",
                    disabled=True,
                    row=1,
                )
            )
        self.index = 0

    def _get_embed(self) -> discord.Embed:
        result = self.results[self.index]
        if result.overview_eng:
            overview = f"{result.overview_eng}"
        elif not result.overview_eng and result.overview:
            overview = f"{result.overview}\n\n*No English overview available.*"
        else:
            overview = "*No overview available.*"
        title = result.bilingual_name
        if result.entity_type == "Movie":
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
            raise ValueError("Dropdown values are empty or not a string but callback was triggered.")
        self.index = int(self.dropdown.values[0])
        if not self.message:
            raise ValueError("Message is not set but callback was triggered.")
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
        required=False,
    )
    @option("by_id", input_type=bool, description="Search by tvdb ID.", required=False)
    async def search(
        self,
        ctx: ApplicationContext,
        *,
        query: str,
        entity_type: Literal["movie", "series"] | None = None,
        by_id: bool = False,
    ) -> None:
        """Search for a movie or series."""
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            client = TvdbClient(session, self.bot.cache)
            if by_id:
                if query.startswith("movie-"):
                    entity_type = "movie"
                    query = query[6:]
                elif query.startswith("series-"):
                    entity_type = "series"
                    query = query[7:]
                try:
                    match entity_type:
                        case "movie":
                            response = [await Movie.fetch(query, client, extended=True, meta=FetchMeta.TRANSLATIONS)]
                        case "series":
                            response = [await Series.fetch(query, client, extended=True, meta=FetchMeta.TRANSLATIONS)]
                        case None:
                            await ctx.respond(
                                "You must specify a type (movie or series) when searching by ID.", ephemeral=True
                            )
                            return
                except InvalidIdError:
                    await ctx.respond(
                        'Invalid ID. Id must be an integer, or "movie-" / "series-" followed by an integer.',
                        ephemeral=True,
                    )
                    return
            else:
                response = await client.search(query, limit=5, entity_type=entity_type)
                if not response:
                    await ctx.respond("No results found.")
                    return
        view = InfoView(response)
        await view.send(ctx)


def setup(bot: Bot) -> None:
    """Register the PingCog cog."""
    bot.add_cog(InfoCog(bot))

from typing import Literal, cast

from discord import ApplicationContext, Cog, Member, User, option, slash_command

from src.bot import Bot
from src.db_adapters.user import user_get_list_safe, user_get_safe
from src.tvdb import FetchMeta, Movie, Series, TvdbClient
from src.tvdb.errors import InvalidIdError
from src.utils.log import get_logger
from src.utils.ratelimit import rate_limited

from .ui import ProfileView, search_view

log = get_logger(__name__)

MOVIE_EMOJI = "🎬"
SERIES_EMOJI = "📺"


class InfoCog(Cog):
    """Cog to show information about a movie or a series."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.tvdb_client = TvdbClient(self.bot.http_session, self.bot.cache)

    @slash_command()
    @option("user", input_type=User, description="The user to show the profile for.", required=False)
    async def profile(self, ctx: ApplicationContext, *, user: User | Member | None = None) -> None:
        """Show a user's profile."""
        await ctx.defer()

        if user is None:
            user = cast(User | Member, ctx.user)  # for some reason, pyright thinks user can be None here

        # Convert Member to User (Member isn't a subclass of User...)
        if isinstance(user, Member):
            user = user._user  # pyright: ignore[reportPrivateUsage]

        # TODO: Friend check (don't allow looking at other people's profiles, unless
        # they are friends with the user, or it's their own profile)
        # https://github.com/ItsDrike/code-jam-2024/issues/51

        db_user = await user_get_safe(self.bot.db_session, user.id)
        view = ProfileView(
            bot=self.bot,
            tvdb_client=self.tvdb_client,
            user=user,
            watched_list=await user_get_list_safe(self.bot.db_session, db_user, "watched"),
            favorite_list=await user_get_list_safe(self.bot.db_session, db_user, "favorite"),
        )
        await view.send(ctx.interaction)

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
    @rate_limited(key=lambda self, ctx: f"{ctx.user}", limit=2, period=8, update_when_exceeded=True, prefix_key=True)
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
                        response = [
                            await Movie.fetch(query, self.tvdb_client, extended=True, meta=FetchMeta.TRANSLATIONS)
                        ]
                    case "series":
                        series = await Series.fetch(
                            query, self.tvdb_client, extended=True, meta=FetchMeta.TRANSLATIONS
                        )
                        await series.fetch_episodes()
                        response = [series]
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
            response = await self.tvdb_client.search(query, limit=5, entity_type=entity_type)
            for element in response:
                await element.ensure_translations()
                if isinstance(element, Series):
                    await element.fetch_episodes()
            if not response:
                await ctx.respond("No results found.")
                return

        view = await search_view(self.bot, ctx.user.id, response)
        await view.send(ctx.interaction)


def setup(bot: Bot) -> None:
    """Register the PingCog cog."""
    bot.add_cog(InfoCog(bot))

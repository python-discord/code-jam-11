import textwrap
from typing import TYPE_CHECKING, final

import discord

from src.bot import Bot
from src.db_adapters import refresh_list_items, user_get_list_safe, user_get_safe
from src.db_tables.user_list import UserList, UserListItem, UserListItemKind
from src.settings import MOVIE_EMOJI, SERIES_EMOJI
from src.tvdb import Movie, Series
from src.tvdb.client import Episode, FetchMeta, TvdbClient
from src.utils.log import get_logger

if TYPE_CHECKING:
    from src.db_tables.user import User

log = get_logger(__name__)


@final
class ProfileView(discord.ui.View):
    """View for displaying user profiles with data about the user's added shows."""

    def __init__(self, bot: Bot, tvdb_client: TvdbClient, user: discord.User) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.tvdb_client = tvdb_client
        self.discord_user = user
        self.user: User
        self.watched_list: UserList
        self.favorite_list: UserList

        self.watched_items: list[Episode | Series | Movie]
        self.favorite_items: list[Episode | Series | Movie]
        self.fetched_series: dict[int, Series] = {}
        self.watched_episodes: set[UserListItem] = set()
        self.watched_episodes_ids: set[int] = set()

    async def _get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Profile",
            description=f"Profile for {self.discord_user.mention}",
            color=discord.Color.blurple(),
            thumbnail=self.discord_user.display_avatar.url,
        )

        total_movies = len([item for item in self.watched_items if isinstance(item, Movie)])
        total_series = len(self.fetched_series)
        total_episodes = len([item for item in self.watched_items if isinstance(item, Episode)])
        stats_str = textwrap.dedent(
            f"""
            **Total Shows:** {total_series} ({total_episodes} episode{'s' if total_episodes > 0 else ''})
            **Total Movies:** {total_movies}
            """
        )
        embed.add_field(name="Stats", value=stats_str, inline=False)

        # TODO: This currently skips showing episodes, however, the entire system of series
        # getting marked as watched should be reworked to use the latest episode in the series
        # which will then need to be handled here. Currently, since a series can be marked
        # as watched regardless of the status of its episodes, just use the series.

        # TODO: What if there's too many things here, we might need to paginate this.

        embed.add_field(
            name="Favorites",
            value="\n".join(
                f"{MOVIE_EMOJI if isinstance(item, Movie) else SERIES_EMOJI} {item.bilingual_name}"
                for item in self.favorite_items
                if not isinstance(item, Episode)
            ),
        )
        watched_str: str = ""
        for item in self.watched_items:
            if isinstance(item, Movie):
                watched_str += f"{MOVIE_EMOJI} {item.bilingual_name}\n"
        for series in self.fetched_series.values():
            if not series.episodes:
                continue
            for i, episode in enumerate(reversed(series.episodes)):
                if episode.id in self.watched_episodes_ids:
                    watched_str += (
                        f"{SERIES_EMOJI} {series.bilingual_name} - {episode.formatted_name if i != 0 else 'entirely'}"
                    )

        embed.add_field(
            name="Watched",
            value=watched_str,
        )
        return embed

    async def _fetch_media(self, item: UserListItem) -> Episode | Series | Movie:
        """Fetch given user list item from database."""
        match item.kind:
            case UserListItemKind.EPISODE:
                return await Episode.fetch(item.tvdb_id, client=self.tvdb_client)
            case UserListItemKind.MOVIE:
                return await Movie.fetch(item.tvdb_id, client=self.tvdb_client)
            case UserListItemKind.SERIES:
                return await Series.fetch(item.tvdb_id, client=self.tvdb_client)

    async def _update_states(self) -> None:
        if not hasattr(self, "user"):
            self.user = await user_get_safe(self.bot.db_session, self.discord_user.id)

        # TODO: Currently, this will result in a lot of API calls and we really just need
        # the names of the items. We should consider storing those in the database directly.
        # (note: what if the name changes? can that even happen?)

        if not hasattr(self, "watched_items"):
            self.watched_list = await user_get_list_safe(self.bot.db_session, self.user, "watched")
        await refresh_list_items(self.bot.db_session, self.watched_list)
        self.watched_items = [
            await self._fetch_media(item) for item in self.watched_list.items if item.kind != UserListItemKind.EPISODE
        ]
        self.watched_episodes = {item for item in self.watched_list.items if item.kind == UserListItemKind.EPISODE}
        self.watched_episodes_ids = {item.tvdb_id for item in self.watched_episodes}
        for episode in self.watched_episodes:
            await self.bot.db_session.refresh(episode, ["episode"])
            if not self.fetched_series.get(episode.episode.series_id):
                series = await Series.fetch(
                    episode.episode.series_id, client=self.tvdb_client, extended=True, meta=FetchMeta.TRANSLATIONS
                )
                await series.fetch_episodes()
                self.fetched_series[episode.episode.series_id] = series

        if not hasattr(self, "favorite_list"):
            self.favorite_list = await user_get_list_safe(self.bot.db_session, self.user, "favorite")
        await refresh_list_items(self.bot.db_session, self.favorite_list)
        self.favorite_items = [await self._fetch_media(item) for item in self.favorite_list.items]

    async def send(self, interaction: discord.Interaction) -> None:
        """Send the view."""
        await self._update_states()
        await interaction.respond(embed=await self._get_embed(), view=self)

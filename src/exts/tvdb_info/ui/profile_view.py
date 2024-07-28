import textwrap
from itertools import groupby
from typing import final

import discord

from src.bot import Bot
from src.db_adapters import refresh_list_items
from src.db_tables.media import Episode as EpisodeTable, Movie as MovieTable, Series as SeriesTable
from src.db_tables.user_list import UserList, UserListItemKind
from src.exts.error_handler.view import ErrorHandledView
from src.settings import MOVIE_EMOJI, SERIES_EMOJI
from src.tvdb import Movie, Series
from src.tvdb.client import FetchMeta, TvdbClient
from src.utils.iterators import get_first
from src.utils.log import get_logger

log = get_logger(__name__)


@final
class ProfileView(ErrorHandledView):
    """View for displaying user profiles with data about the user's added shows."""

    fetched_favorite_movies: list[Movie]
    fetched_favorite_shows: list[Series]
    fetched_watched_movies: list[Movie]
    fetched_watched_shows: list[Series]
    fetched_partially_watched_shows: list[Series]
    episodes_total: int

    def __init__(
        self,
        *,
        bot: Bot,
        tvdb_client: TvdbClient,
        user: discord.User,
        watched_list: UserList,
        favorite_list: UserList,
    ) -> None:
        super().__init__()
        self.bot = bot
        self.tvdb_client = tvdb_client
        self.discord_user = user
        self.watched_list = watched_list
        self.favorite_list = favorite_list

    async def _initialize(self) -> None:
        """Initialize the view, obtaining any necessary state."""
        await refresh_list_items(self.bot.db_session, self.watched_list)
        await refresh_list_items(self.bot.db_session, self.favorite_list)

        watched_movies: list[MovieTable] = []
        watched_shows: list[SeriesTable] = []
        partially_watched_shows: list[SeriesTable] = []
        watched_episodes: list[EpisodeTable] = []

        for item in self.watched_list.items:
            match item.kind:
                case UserListItemKind.MOVIE:
                    await self.bot.db_session.refresh(item, ["movie"])
                    watched_movies.append(item.movie)
                case UserListItemKind.SERIES:
                    await self.bot.db_session.refresh(item, ["series"])
                    watched_shows.append(item.series)
                case UserListItemKind.EPISODE:
                    await self.bot.db_session.refresh(item, ["episode"])
                    await self.bot.db_session.refresh(item.episode, ["series"])
                    watched_episodes.append(item.episode)

        # We don't actually care about episodes in the profile view, however, we need them
        # because of the way shows are marked as watched (last episode watched -> show watched).

        for series_id, episodes in groupby(watched_episodes, key=lambda x: x.series_id):
            series = await Series.fetch(series_id, client=self.tvdb_client, extended=True, meta=FetchMeta.EPISODES)
            if series.episodes is None:
                raise ValueError("Found an episode in watched list for a series with no episodes")

            last_episode = get_first(episode for episode in reversed(series.episodes) if episode.aired)
            if not last_episode or last_episode.id is None:
                raise ValueError("Episode has no ID or is None")

            episodes_it = iter(episodes)
            first_db_episode = get_first(episodes_it)
            if first_db_episode is None:
                raise ValueError("No episodes found in a group (never)")

            group_episode_ids = {episode.tvdb_id for episode in episodes_it}
            group_episode_ids.add(first_db_episode.tvdb_id)
            await self.bot.db_session.refresh(first_db_episode, ["series"])

            if first_db_episode.series is None:  # pyright: ignore[reportUnnecessaryComparison]
                manual = await self.bot.db_session.get(SeriesTable, first_db_episode.series_id)
                raise ValueError(f"DB series is None id={first_db_episode.series_id}, manual={manual}")

            if last_episode.id in group_episode_ids:
                watched_shows.append(first_db_episode.series)
            else:
                partially_watched_shows.append(first_db_episode.series)

        favorite_movies: list[MovieTable] = []
        favorite_shows: list[SeriesTable] = []

        for item in self.favorite_list.items:
            match item.kind:
                case UserListItemKind.MOVIE:
                    await self.bot.db_session.refresh(item, ["movie"])
                    favorite_movies.append(item.movie)
                case UserListItemKind.SERIES:
                    await self.bot.db_session.refresh(item, ["series"])
                    favorite_shows.append(item.series)
                case UserListItemKind.EPISODE:
                    raise TypeError("Found an episode in favorite list")

        # Fetch the data about all favorite & watched items from tvdb
        # TODO: This is a lot of API calls, we should probably limit this to some maximum
        self.fetched_favorite_movies = [
            await Movie.fetch(media_db_data.tvdb_id, client=self.tvdb_client) for media_db_data in favorite_movies
        ]
        self.fetched_favorite_shows = [
            await Series.fetch(
                media_db_data.tvdb_id, client=self.tvdb_client, extended=True, meta=FetchMeta.TRANSLATIONS
            )
            for media_db_data in favorite_shows
        ]
        self.fetched_watched_movies = [
            await Movie.fetch(media_db_data.tvdb_id, client=self.tvdb_client) for media_db_data in watched_movies
        ]
        self.fetched_watched_shows = [
            await Series.fetch(
                media_db_data.tvdb_id,
                client=self.tvdb_client,
                extended=True,
                meta=FetchMeta.TRANSLATIONS,
            )
            for media_db_data in watched_shows
        ]
        self.fetched_partially_watched_shows = [
            await Series.fetch(
                media_db_data.tvdb_id,
                client=self.tvdb_client,
                extended=True,
                meta=FetchMeta.TRANSLATIONS,
            )
            for media_db_data in partially_watched_shows
        ]

        # Instead of fetching all episodes, just store the total number of episodes that the user has added
        # as that's the only thing we need here and while it is a bit inconsistent, it's a LOT more efficient.
        self.episodes_total = len(watched_episodes)

    def _get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Profile",
            description=f"Profile for {self.discord_user.mention}",
            color=discord.Color.blurple(),
            thumbnail=self.discord_user.display_avatar.url,
        )

        stats_str = textwrap.dedent(
            f"""
            **Total Shows:** {len(self.fetched_watched_shows)} \
            ({self.episodes_total} episode{'s' if self.episodes_total > 0 else ''})
            **Total Movies:** {len(self.fetched_watched_movies)}
            """
        )
        embed.add_field(name="Stats", value=stats_str, inline=False)

        # TODO: What if there's too many things here, we might need to paginate this.

        favorite_items: list[str] = []
        for item in self.fetched_favorite_movies:
            favorite_items.append(f"[{MOVIE_EMOJI} {item.bilingual_name}]({item.url})")  # noqa: PERF401
        for item in self.fetched_favorite_shows:
            favorite_items.append(f"[{SERIES_EMOJI} {item.bilingual_name}]({item.url})")  # noqa: PERF401

        embed.add_field(
            name="Favorites",
            value="\n".join(favorite_items) or "No favorites",
        )
        watched_items: list[str] = []
        for item in self.fetched_watched_movies:
            watched_items.append(f"[{MOVIE_EMOJI} {item.bilingual_name}]({item.url})")  # noqa: PERF401
        for item in self.fetched_watched_shows:
            watched_items.append(f"[{SERIES_EMOJI} {item.bilingual_name}]({item.url})")  # noqa: PERF401
        for item in self.fetched_partially_watched_shows:
            watched_items.append(f"[{SERIES_EMOJI} {item.bilingual_name}]({item.url}) partially")  # noqa: PERF401

        embed.add_field(
            name="Watched",
            value="\n".join(watched_items) or "No watched items",
        )
        return embed

    async def send(self, interaction: discord.Interaction) -> None:
        """Send the view."""
        await self._initialize()
        await interaction.respond(embed=self._get_embed(), view=self)

from typing import Literal, final, override

import discord

from src.bot import Bot
from src.db_adapters.lists import (
    get_list_item,
    list_put_item,
    list_put_item_safe,
    list_remove_item,
    list_remove_item_safe,
    refresh_list_items,
)
from src.db_tables.user_list import UserList, UserListItemKind
from src.settings import MOVIE_EMOJI, SERIES_EMOJI, THETVDB_COPYRIGHT_FOOTER, THETVDB_LOGO
from src.tvdb.client import Movie, Series
from src.utils.iterators import get_first

from ._media_view import MediaView
from .episode_view import EpisodeView


class _SeriesOrMovieView(MediaView):
    """View for displaying details about a movie or a series."""

    @override
    def __init__(
        self,
        *,
        bot: Bot,
        user_id: int,
        invoker_user_id: int,
        watched_list: UserList,
        favorite_list: UserList,
        media_data: Movie | Series,
    ) -> None:
        super().__init__(
            bot=bot,
            user_id=user_id,
            invoker_user_id=invoker_user_id,
            watched_list=watched_list,
            favorite_list=favorite_list,
        )

        self.media_data = media_data

    @property
    def _db_item_kind(self) -> Literal[UserListItemKind.MOVIE, UserListItemKind.SERIES]:
        """Return the kind of item this view represents."""
        if isinstance(self.media_data, Series):
            return UserListItemKind.SERIES
        return UserListItemKind.MOVIE

    @override
    async def is_favorite(self) -> bool:
        if not self.media_data.id:
            raise ValueError("Media has no ID")

        item = await get_list_item(self.bot.db_session, self.favorite_list, self.media_data.id, self._db_item_kind)
        return item is not None

    @override
    async def set_favorite(self, state: bool) -> None:
        if not self.media_data.id:
            raise ValueError("Media has no ID")

        if state is False:
            item = await get_list_item(self.bot.db_session, self.favorite_list, self.media_data.id, self._db_item_kind)
            if item is None:
                raise ValueError("Media is not marked as favorite, can't re-mark as favorite.")
            await list_remove_item(self.bot.db_session, self.watched_list, item)
        else:
            try:
                await list_put_item(self.bot.db_session, self.favorite_list, self.media_data.id, self._db_item_kind)
            except ValueError:
                raise ValueError("Media is already marked as favorite, can't re-mark as favorite.")

    @override
    async def is_watched(self) -> bool:
        if not self.media_data.id:
            raise ValueError("Media has no ID")

        item = await get_list_item(self.bot.db_session, self.watched_list, self.media_data.id, self._db_item_kind)
        return item is not None

    @override
    async def set_watched(self, state: bool) -> None:
        if not self.media_data.id:
            raise ValueError("Media has no ID")

        if state is False:
            item = await get_list_item(self.bot.db_session, self.watched_list, self.media_data.id, self._db_item_kind)
            if item is None:
                raise ValueError("Media is not marked as watched, can't re-mark as unwatched.")
            await list_remove_item(self.bot.db_session, self.watched_list, item)
        else:
            try:
                await list_put_item(self.bot.db_session, self.watched_list, self.media_data.id, self._db_item_kind)
            except ValueError:
                raise ValueError("Media is already marked as watched, can't re-mark as watched.")

    @override
    def _get_embed(self) -> discord.Embed:
        if self.media_data.overview_eng:
            overview = f"{self.media_data.overview_eng}"
            overview_extra = ""
        elif not self.media_data.overview_eng and self.media_data.overview:
            overview = f"{self.media_data.overview}"
            overview_extra = "*No English overview available.*"
        else:
            overview = ""
            overview_extra = "*No overview available.*"

        if len(overview) > 1000:
            overview = overview[:100] + "..."

        if overview_extra:
            if overview:
                overview += f"\n\n{overview_extra}"
            else:
                overview = overview_extra

        title = self.media_data.bilingual_name

        if isinstance(self.media_data, Series):
            title = f"{SERIES_EMOJI} {title}"
        else:
            title = f"{MOVIE_EMOJI} {title}"
        url = self.media_data.url

        embed = discord.Embed(title=title, color=discord.Color.blurple(), url=url)
        embed.add_field(name="Overview", value=overview, inline=False)
        embed.set_footer(text=THETVDB_COPYRIGHT_FOOTER, icon_url=THETVDB_LOGO)
        embed.set_image(url=self.media_data.image_url)
        return embed


@final
class SeriesView(_SeriesOrMovieView):
    """View for displaying details about a series."""

    media_data: Series

    @override
    def __init__(
        self,
        *,
        bot: Bot,
        user_id: int,
        invoker_user_id: int,
        watched_list: UserList,
        favorite_list: UserList,
        media_data: Series,
    ) -> None:
        super().__init__(
            bot=bot,
            user_id=user_id,
            invoker_user_id=invoker_user_id,
            watched_list=watched_list,
            favorite_list=favorite_list,
            media_data=media_data,
        )

        self.episodes_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="View episodes",
            emoji="📺",
            row=1,
        )
        self.episodes_button.callback = self._episodes_button_callback

    @override
    async def _initialize(self) -> None:
        await self.media_data.ensure_seasons_and_episodes()
        await super()._initialize()

    @override
    def _add_items(self) -> None:
        super()._add_items()
        self.add_item(self.episodes_button)

    async def _episodes_button_callback(self, interaction: discord.Interaction) -> None:
        """Callback for when the user clicks the "View Episodes" button."""
        if not await self._ensure_correct_invoker(interaction):
            return

        view = EpisodeView(
            bot=self.bot,
            user_id=self.user_id,
            invoker_user_id=self.invoker_user_id,
            watched_list=self.watched_list,
            favorite_list=self.favorite_list,
            series=self.media_data,
        )
        await view.send(interaction)

    @override
    async def is_watched(self) -> bool:
        # Series uses a special method to determine whether it's watched.
        # This approach uses the last episode of the series to determine if the series is watched.

        # If the series has no episodes, fall back to marking the series itself as watched.
        if self.media_data.episodes is None:
            return await super().is_watched()

        last_ep = get_first(episode for episode in reversed(self.media_data.episodes) if episode.aired)

        if not last_ep or last_ep.id is None:
            raise ValueError("Episode has no ID")

        item = await get_list_item(self.bot.db_session, self.watched_list, last_ep.id, UserListItemKind.EPISODE)
        return item is not None

    @override
    async def set_watched(self, state: bool) -> None:
        # When a series is marked as watched, we mark all of its aired episodes as watched.
        # Similarly, unmarking will unmark all episodes (aired or not).

        # If the series has no episodes, fall back to marking the season itself as watched / unwatched.
        if self.media_data.episodes is None:
            await super().set_watched(state)
            return

        if state is False:
            for episode in self.media_data.episodes:
                if not episode.id:
                    raise ValueError("Episode has no ID")

                await list_remove_item_safe(
                    self.bot.db_session,
                    self.watched_list,
                    episode.id,
                    UserListItemKind.EPISODE,
                )

            await refresh_list_items(self.bot.db_session, self.watched_list)
        else:
            for episode in self.media_data.episodes:
                if not episode.id:
                    raise ValueError("Episode has no ID")
                if not episode.aired:
                    continue

                await list_put_item_safe(
                    self.bot.db_session,
                    self.watched_list,
                    episode.id,
                    UserListItemKind.EPISODE,
                    self.media_data.id,
                )


@final
class MovieView(_SeriesOrMovieView):
    """View for displaying details about a movie."""

    media_data: Movie

    # We override __init__ to provide a more specific type for media_data
    @override
    def __init__(
        self,
        *,
        bot: Bot,
        user_id: int,
        invoker_user_id: int,
        watched_list: UserList,
        favorite_list: UserList,
        media_data: Movie,
    ) -> None:
        super().__init__(
            bot=bot,
            user_id=user_id,
            invoker_user_id=invoker_user_id,
            watched_list=watched_list,
            favorite_list=favorite_list,
            media_data=media_data,
        )

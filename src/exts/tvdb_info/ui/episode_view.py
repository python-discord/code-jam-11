import warnings
from typing import final, override

import discord

from src.bot import Bot
from src.db_adapters.lists import get_list_item, list_put_item, list_remove_item
from src.db_tables.user_list import UserList, UserListItemKind
from src.settings import THETVDB_COPYRIGHT_FOOTER, THETVDB_LOGO
from src.tvdb.client import Episode, Series
from src.utils.tvdb import by_season

from ._media_view import DynamicMediaView


@final
class EpisodeView(DynamicMediaView):
    """View for displaying episodes of a series."""

    def __init__(
        self,
        *,
        bot: Bot,
        user_id: int,
        watched_list: UserList,
        favorite_list: UserList,
        series: Series,
        season_idx: int = 1,
        episode_idx: int = 1,
    ) -> None:
        super().__init__(bot=bot, user_id=user_id, watched_list=watched_list, favorite_list=favorite_list)

        self.series = series

        self.season_idx = season_idx
        self.episode_idx = episode_idx

        self.episode_dropdown = discord.ui.Select(placeholder="Select an episode")
        self.episode_dropdown.callback = self._episode_dropdown_callback

        self.season_dropdown = discord.ui.Select(placeholder="Select a season")
        self.season_dropdown.callback = self._season_dropdown_callback

        self.watched_button.row = 2
        self.favorite_button.row = 2

    @override
    def _add_items(self) -> None:
        self.add_item(self.episode_dropdown)
        self.add_item(self.season_dropdown)
        super()._add_items()

        # Episodes aren't favoritable
        self.remove_item(self.favorite_button)

    @override
    async def _initialize(self) -> None:
        await self.series.ensure_seasons_and_episodes()
        if self.series.episodes is None:
            raise ValueError("Series has no episodes")
        self.episodes = by_season(self.series.episodes)

        # Make the super call (must happen after we set self.episodes)
        # This assumes is_favorite works properly, however, since we don't actually have
        # this implemented for episodes, to make this call work, we'll need to temporarily
        # set is_favorite to a dummy method.
        _old_is_favorite = self.is_favorite

        async def _dummy_is_favorite() -> bool:
            return False

        self.is_favorite = _dummy_is_favorite
        await super()._initialize()
        self.is_favorite = _old_is_favorite

    @override
    async def _update_state(self) -> None:
        self.episode_dropdown.options = [
            discord.SelectOption(
                label=episode.formatted_name,
                value=str(episode.number),
                description=episode.overview[:100] if episode.overview else None,
            )
            for episode in self.episodes[self.season_idx]
        ]

        self.season_dropdown.options = [
            discord.SelectOption(label=f"Season {season}", value=str(season)) for season in self.episodes
        ]

        # TODO: This is not ideal, we should support some way to paginate this, however
        # implementing that isn't trivial. For now, just trim the list to prevent errors.

        if len(self.episode_dropdown.options) > 25:
            self.episode_dropdown.options = self.episode_dropdown.options[:25]
            warnings.warn("Too many episodes to display, truncating to 25", UserWarning, stacklevel=1)

        if len(self.season_dropdown.options) > 25:
            self.season_dropdown.options = self.season_dropdown.options[:25]
            warnings.warn("Too many seasons to display, truncating to 25", UserWarning, stacklevel=1)

    @property
    def current_episode(self) -> "Episode":
        """Get the current episode being displayed."""
        return self.episodes[self.season_idx][self.episode_idx - 1]

    @override
    async def is_favorite(self) -> bool:
        raise NotImplementedError("Individual episodes cannot be marked as favorite.")

    @override
    async def set_favorite(self, state: bool) -> None:
        raise NotImplementedError("Individual episodes cannot be marked as favorite.")

    @override
    async def is_watched(self) -> bool:
        if not self.current_episode.id:
            raise ValueError("Episode has no ID")

        item = await get_list_item(
            self.bot.db_session,
            self.watched_list,
            self.current_episode.id,
            UserListItemKind.EPISODE,
        )
        return item is not None

    @override
    async def set_watched(self, state: bool) -> None:
        if not self.current_episode.id:
            raise ValueError("Episode has no ID")

        if state is False:
            item = await get_list_item(
                self.bot.db_session,
                self.watched_list,
                self.current_episode.id,
                UserListItemKind.EPISODE,
            )
            if item is None:
                raise ValueError("Episode is not marked as watched, can't re-mark as unwatched.")
            await list_remove_item(self.bot.db_session, self.watched_list, item)
        else:
            try:
                await list_put_item(
                    self.bot.db_session,
                    self.watched_list,
                    self.current_episode.id,
                    UserListItemKind.EPISODE,
                    self.series.id,
                )
            except ValueError:
                raise ValueError("Episode is already marked as watched, can't re-mark as watched.")

    async def _episode_dropdown_callback(self, interaction: discord.Interaction) -> None:
        """Callback for when the user selects an episode from the drop-down."""
        if not self.episode_dropdown.values or not isinstance(self.episode_dropdown.values[0], str):
            raise ValueError("Episode dropdown values are empty or non-string, but callback was triggered.")

        new_episode_idx = int(self.episode_dropdown.values[0])
        if new_episode_idx == self.episode_idx:
            await interaction.response.defer()
            return

        self.episode_idx = new_episode_idx
        await self._update_state()
        await interaction.response.defer()
        await self._refresh()

    async def _season_dropdown_callback(self, interaction: discord.Interaction) -> None:
        """Callback for when the user selects a season from the drop-down."""
        if not self.season_dropdown.values or not isinstance(self.season_dropdown.values[0], str):
            raise ValueError("Episode dropdown values are empty or non-string, but callback was triggered.")

        new_season_idx = int(self.season_dropdown.values[0])
        if new_season_idx == self.season_idx:
            await interaction.response.defer()
            return

        self.season_idx = new_season_idx
        self.episode_idx = 1
        await self._update_state()
        await interaction.response.defer()
        await self._refresh()

    @override
    def _get_embed(self) -> discord.Embed:
        if self.current_episode.overview:
            description = self.current_episode.overview
            if len(description) > 1000:
                description = description[:1000] + "..."
        else:
            description = None

        embed = discord.Embed(
            title=self.current_episode.formatted_name,
            description=description,
            color=discord.Color.blurple(),
            url=f"https://www.thetvdb.com/series/{self.series.slug}",
        )
        embed.set_image(url=f"https://www.thetvdb.com{self.current_episode.image}")
        embed.set_footer(text=THETVDB_COPYRIGHT_FOOTER, icon_url=THETVDB_LOGO)
        return embed

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import NamedTuple, Self, TYPE_CHECKING, TypedDict, override

import discord

from src.bot import Bot
from src.db_adapters import (
    get_list_item,
    list_put_item,
    list_put_item_safe,
    list_remove_item,
    list_remove_item_safe,
    refresh_list_items,
    user_get_list_safe,
    user_get_safe,
)
from src.db_tables.user_list import UserList, UserListItem, UserListItemKind
from src.settings import THETVDB_COPYRIGHT_FOOTER, THETVDB_LOGO
from src.tvdb import Movie, Series
from src.utils.log import get_logger
from src.utils.tvdb import by_season

if TYPE_CHECKING:
    from src.db_tables.user import User
    from src.tvdb.client import Episode

log = get_logger(__name__)

MOVIE_EMOJI = "🎬"
SERIES_EMOJI = "📺"


class ReactiveButtonState(TypedDict):
    """Type definition for a reactive button state."""

    label: str
    style: discord.ButtonStyle
    emoji: str


class ReactiveButton[V: discord.ui.View](NamedTuple):
    """A tuple of the button, the item in the list, the state when active, and the state when inactive.

    This allows us to programmatically change the button's appearance based on the state of the item in the list.
    """

    button: discord.ui.Button[V]
    item: UserListItem | None
    active_state: ReactiveButtonState
    inactive_state: ReactiveButtonState


class _ReactiveView(discord.ui.View, ABC):
    _reactive_buttons_store: list[ReactiveButton[Self]] | None = None
    bot: Bot
    refreshing: bool = False

    async def _update_states(self) -> None:
        for button, item, active_state, inactive_state in await self._reactive_buttons:
            if item:
                button.style = inactive_state["style"]
                button.label = inactive_state["label"]
                button.emoji = inactive_state["emoji"]
            else:
                button.style = active_state["style"]
                button.label = active_state["label"]
                button.emoji = active_state["emoji"]

    async def _refresh(self) -> None:
        await self._update_states()
        if not self.message:
            raise ValueError("Message is not set but refresh was called.")
        await self.message.edit(embed=self._get_embed(), view=self)

    @abstractmethod
    def _get_embed(self) -> discord.Embed:
        """Get the embed for the view."""

    @abstractmethod
    async def send(self, interaction: discord.Interaction) -> None:
        """Send the view."""

    @property
    @abstractmethod
    async def _reactive_buttons(self) -> list[ReactiveButton[Self]]:
        """Get the reactive buttons."""

    async def _current_list_item(
        self,
        user_list: UserList,
        store: UserListItem | None,
        tvdb_id: int | None,
        kind: UserListItemKind,
    ) -> UserListItem | None:
        """Get the current list item from the store or the database."""
        if not tvdb_id:
            raise ValueError("TVDB ID is not set but callback was triggered.")
        if not (store and store.tvdb_id == tvdb_id):
            store = await get_list_item(self.bot.db_session, user_list, tvdb_id, kind)
        return store


class EpisodeView(_ReactiveView):
    """View for displaying episodes of a series and interacting with them."""

    def __init__(
        self, bot: Bot, user_id: int, series: Series, watched_list: UserList, favorite_list: UserList
    ) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.series = series
        self.user: User
        self.watched_list = watched_list
        self.favorite_list = favorite_list
        self.episodes: dict[int, list[Episode]]
        self.season_idx: int = 1
        self.episode_idx: int = 1

        self._reactive_buttons_store: list[ReactiveButton[Self]] | None = None
        self._current_watched_list_item_store: UserListItem | None = None
        self._current_favorite_list_item_store: UserListItem | None = None

        self.episode_dropdown = discord.ui.Select(
            placeholder="Select an episode",
        )
        self.episode_dropdown.callback = self._episode_dropdown_callback
        self.add_item(self.episode_dropdown)

        self.season_dropdown = discord.ui.Select(
            placeholder="Select a season",
        )
        self.season_dropdown.callback = self._season_dropdown_callback
        self.add_item(self.season_dropdown)

        self.watched_btn = discord.ui.Button(
            row=2,
        )
        self.watched_btn.callback = self._watched_callback
        self.add_item(self.watched_btn)

        self.favorite_btn = discord.ui.Button(
            row=2,
        )
        self.favorite_btn.callback = self._favorite_callback
        self.add_item(self.favorite_btn)

    @property
    @override
    async def _reactive_buttons(self) -> list[ReactiveButton[Self]]:
        if self._reactive_buttons_store:
            return self._reactive_buttons_store
        return [
            ReactiveButton(
                self.watched_btn,
                await self._current_watched_list_item,
                {
                    "label": "Mark as watched",
                    "style": discord.ButtonStyle.success,
                    "emoji": "✅",
                },
                {
                    "label": "Unmark as watched",
                    "style": discord.ButtonStyle.primary,
                    "emoji": "❌",
                },
            ),
            ReactiveButton(
                self.favorite_btn,
                await self._current_favorite_list_item,
                {
                    "label": "Favorite",
                    "style": discord.ButtonStyle.primary,
                    "emoji": "⭐",
                },
                {
                    "label": "Unfavorite",
                    "style": discord.ButtonStyle.secondary,
                    "emoji": "❌",
                },
            ),
        ]

    @property
    def _current_episode(self) -> "Episode":
        return self.episodes[self.season_idx][self.episode_idx - 1]

    @property
    async def _current_watched_list_item(self) -> UserListItem | None:
        return await self._current_list_item(
            self.watched_list,
            self._current_watched_list_item_store,
            self._current_episode.id,
            UserListItemKind.EPISODE,
        )

    @property
    async def _current_favorite_list_item(self) -> UserListItem | None:
        return await self._current_list_item(
            self.favorite_list,
            self._current_favorite_list_item_store,
            self._current_episode.id,
            UserListItemKind.EPISODE,
        )

    async def _mark_callback(self, user_list: UserList, item: UserListItem | None) -> bool:
        """Mark or unmark an item in a list.

        :param user_list:
        :param item:
        :return:
        """
        if item:
            await list_remove_item(self.bot.db_session, user_list, item)
            return False
        if not self._current_episode.id:
            raise ValueError("Current episode has no ID but callback was triggered.")
        await list_put_item(
            self.bot.db_session,
            user_list,
            self._current_episode.id,
            UserListItemKind.EPISODE,
            self.series.id,
        )
        return True

    async def _watched_callback(self, interaction: discord.Interaction) -> None:
        """Callback for marking an episode as watched."""
        await interaction.response.defer()

        await self._mark_callback(self.watched_list, await self._current_watched_list_item)

        await self._refresh()

    async def _favorite_callback(self, interaction: discord.Interaction) -> None:
        """Callback for favoriting an episode."""
        await interaction.response.defer()

        await self._mark_callback(self.favorite_list, await self._current_favorite_list_item)

        await self._refresh()

    @override
    async def _update_states(self) -> None:
        if not hasattr(self, "user"):
            self.user = await user_get_safe(self.bot.db_session, self.user_id)
        await refresh_list_items(self.bot.db_session, self.watched_list)
        await refresh_list_items(self.bot.db_session, self.favorite_list)

        if self.series.episodes:
            self.episodes = by_season(self.series.episodes)
        else:
            raise ValueError("Series has no episodes.")

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

        await super()._update_states()

    @override
    def _get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self._current_episode.formatted_name,
            description=self._current_episode.overview,
            color=discord.Color.blurple(),
            url=f"https://www.thetvdb.com/series/{self.series.slug}",
        )
        embed.set_image(url=f"https://www.thetvdb.com{self._current_episode.image}")
        embed.set_footer(text=THETVDB_COPYRIGHT_FOOTER, icon_url=THETVDB_LOGO)
        return embed

    @override
    async def send(self, interaction: discord.Interaction) -> None:
        """Send the view."""
        await self.series.ensure_seasons_and_episodes()
        await self._update_states()
        await interaction.respond(embed=self._get_embed(), view=self)

    async def _episode_dropdown_callback(self, interaction: discord.Interaction) -> None:
        if not self.episode_dropdown.values or not isinstance(self.episode_dropdown.values[0], str):
            raise ValueError("Episode dropdown values are empty or not a string but callback was triggered.")
        self.episode_idx = int(self.episode_dropdown.values[0])
        await self._refresh()
        await interaction.response.defer()

    async def _season_dropdown_callback(self, interaction: discord.Interaction) -> None:
        if not self.season_dropdown.values or not isinstance(self.season_dropdown.values[0], str):
            raise ValueError("Season dropdown values are empty or not a string but callback was triggered.")
        self.season_idx = int(self.season_dropdown.values[0])
        self.episode_idx = 1
        await self._refresh()
        await interaction.response.defer()


class InfoView(_ReactiveView):
    """View for displaying information about a movie or series and interacting with it."""

    def __init__(self, bot: Bot, user_id: int, results: Sequence[Movie | Series]) -> None:
        super().__init__(disable_on_timeout=True)
        self.index = 0  # the index of the current result
        self.results = results
        self.bot = bot
        self.user_id = user_id
        self.user: User
        self.watched_list: UserList
        self.favorite_list: UserList

        self._current_watched_list_item_store: UserListItem | None = None
        self._current_favorite_list_item_store: UserListItem | None = None

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

        self.watched_btn = discord.ui.Button(
            # styles are set by the reactive button system and omitted here
            row=1,
        )
        self.watched_btn.callback = self._mark_as_watched_callback
        self.add_item(self.watched_btn)

        self.favorite_btn = discord.ui.Button(
            row=1,
        )
        self.favorite_btn.callback = self._favorite_callback
        self.add_item(self.favorite_btn)
        self._reactive_buttons_store: list[ReactiveButton[Self]] | None = None

        self.episodes_btn: discord.ui.Button[InfoView] | None = None

        if isinstance(self._current_result, Series):
            self.episodes_btn = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="View episodes",
                emoji="📺",
                row=1,
            )
            self.add_item(self.episodes_btn)

            self.episodes_btn.callback = self._episode_callback

    @property
    @override
    async def _reactive_buttons(self) -> list[ReactiveButton[Self]]:
        return [
            ReactiveButton(
                self.watched_btn,
                await self._current_watched_list_item,
                {
                    "label": "Mark all episodes as watched",
                    "style": discord.ButtonStyle.success,
                    "emoji": "✅",
                },
                {
                    "label": "Unmark all episodes as watched",
                    # We avoid using .danger because of bad styling in conjunction with the emoji.
                    # It could be possible to use .danger, but would have to use an emoji that fits better.
                    "style": discord.ButtonStyle.primary,
                    "emoji": "❌",
                },
            ),
            ReactiveButton(
                self.favorite_btn,
                await self._current_favorite_list_item,
                {
                    "label": "Favorite",
                    "style": discord.ButtonStyle.primary,
                    "emoji": "⭐",
                },
                {
                    "label": "Unfavorite",
                    "style": discord.ButtonStyle.secondary,
                    "emoji": "❌",
                },
            ),
        ]

    @property
    def _current_result(self) -> Movie | Series:
        return self.results[self.index]

    @property
    async def _current_watched_list_item(self) -> UserListItem | None:
        if (
            isinstance(self._current_result, Series)
            and self._current_result.episodes
            and self._current_result.episodes[-1].id
        ):
            if (
                not self._current_watched_list_item_store
                or self._current_watched_list_item_store.tvdb_id != self._current_result.episodes[-1].id
                or self.refreshing
            ):
                self._current_watched_list_item_store = await get_list_item(
                    self.bot.db_session,
                    self.watched_list,
                    self._current_result.episodes[-1].id,
                    UserListItemKind.EPISODE,
                )
            return self._current_watched_list_item_store
        return await self._current_list_item(
            self.watched_list, self._current_watched_list_item_store, self._current_result.id, self._current_kind
        )

    @property
    async def _current_favorite_list_item(self) -> UserListItem | None:
        return await self._current_list_item(
            self.favorite_list, self._current_favorite_list_item_store, self._current_result.id, self._current_kind
        )

    @property
    def _current_kind(self) -> UserListItemKind:
        return UserListItemKind.MOVIE if self._current_result.entity_type == "Movie" else UserListItemKind.SERIES

    @override
    def _get_embed(self) -> discord.Embed:
        result = self._current_result
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

    @override
    async def _update_states(self) -> None:
        self.refreshing = True
        if isinstance(self._current_result, Series):
            await self._current_result.ensure_seasons_and_episodes()
        if not hasattr(self, "user"):
            self.user = await user_get_safe(self.bot.db_session, self.user_id)
        if not hasattr(self, "watched_list"):
            self.watched_list = await user_get_list_safe(self.bot.db_session, self.user, "watched")
        await refresh_list_items(self.bot.db_session, self.watched_list)
        if not hasattr(self, "favorite_list"):
            self.favorite_list = await user_get_list_safe(self.bot.db_session, self.user, "favorite")
        await refresh_list_items(self.bot.db_session, self.favorite_list)

        await super()._update_states()
        self.refreshing = False

    async def _dropdown_callback(self, interaction: discord.Interaction) -> None:
        if not self.dropdown.values or not isinstance(self.dropdown.values[0], str):
            raise ValueError("Dropdown values are empty or not a string but callback was triggered.")
        self.index = int(self.dropdown.values[0])
        await self._refresh()
        await interaction.response.defer()

    @override
    async def send(self, interaction: discord.Interaction) -> None:
        """Send the view."""
        await self._update_states()
        await interaction.respond(embed=self._get_embed(), view=self)

    async def _mark_callback(self, user_list: UserList, item: UserListItem | None) -> bool:
        """Mark or unmark an item in a list.

        :param user_list:
        :param item:
        :return:
        """
        if item:
            await list_remove_item(self.bot.db_session, user_list, item)
            return False
        await list_put_item(
            self.bot.db_session,
            user_list,
            self._current_result.id,
            self._current_kind,  # pyright: ignore[reportArgumentType]
        )
        return True

    async def _mark_as_watched_callback(self, interaction: discord.Interaction) -> None:
        """Callback for marking a movie or series as watched."""
        # `defer` technically produces a response to the interaction, and allows us not to respond to the interaction
        # to make the interface feel more intuitive, avoiding unnecessary responses.
        await interaction.response.defer()
        if isinstance(self._current_result, Movie):
            await self._mark_callback(self.watched_list, await self._current_watched_list_item)
        elif await self._current_watched_list_item:
            for episode in self._current_result.episodes:  # pyright: ignore [reportOptionalIterable]
                if not episode.id:
                    continue
                await list_remove_item_safe(
                    self.bot.db_session, self.watched_list, episode.id, UserListItemKind.EPISODE
                )
                await refresh_list_items(self.bot.db_session, self.watched_list)
                await self._current_watched_list_item
        elif self._current_result.episodes and self._current_result.episodes[-1].id:
            for episode in self._current_result.episodes:
                if not episode.id:
                    continue
                await list_put_item_safe(
                    self.bot.db_session,
                    self.watched_list,
                    episode.id,
                    UserListItemKind.EPISODE,
                    self._current_result.id,
                )

        await self._refresh()

    async def _favorite_callback(self, interaction: discord.Interaction) -> None:
        """Callback for favoriting a movie or series."""
        await interaction.response.defer()

        await self._mark_callback(self.favorite_list, await self._current_favorite_list_item)

        await self._refresh()

    async def _episode_callback(self, interaction: discord.Interaction) -> None:
        """Callback for viewing episodes of a series."""
        await interaction.response.defer()
        series = self._current_result
        if not isinstance(series, Series):
            raise TypeError("Current result is not a series but callback was triggered.")
        watched_list = await user_get_list_safe(self.bot.db_session, self.user, "watched")
        favorite_list = await user_get_list_safe(self.bot.db_session, self.user, "favorite")
        view = EpisodeView(self.bot, self.user_id, series, watched_list, favorite_list)
        await view.send(interaction)

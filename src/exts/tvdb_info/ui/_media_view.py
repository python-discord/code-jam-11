from abc import ABC, abstractmethod
from typing import override

import discord

from src.bot import Bot
from src.db_tables.user_list import UserList
from src.exts.error_handler.view import ErrorHandledView

from ._reactive_buttons import ReactiveButton, ReactiveButtonStateStyle


class MediaView(ErrorHandledView, ABC):
    """Base class for views that display info about some media (movie/series/episode)."""

    def __init__(self, *, bot: Bot, user_id: int, watched_list: UserList, favorite_list: UserList) -> None:
        """Initialize MediaView.

        :param bot: The bot instance.
        :param user_id:
            Discord ID of the user that invoked this view.

            Only this user will be able to interact with this view and the relevant information
            will be tailored towards this user based on their data. (i.e. whether they have already
            watched this media / marked it favorite.)
        :param watched_list: The list of all watched items for this user.
        :param favorite_list: The list of all favorited items for this user.
        """
        super().__init__(disable_on_timeout=True)

        self.bot = bot
        self.user_id = user_id
        self.watched_list = watched_list
        self.favorite_list = favorite_list

        self.watched_button = ReactiveButton(
            initial_state=False,  # This should be updated on _initialize
            state_map={
                False: ReactiveButtonStateStyle(
                    label="Mark as watched",
                    style=discord.ButtonStyle.success,
                    emoji="✅",
                ),
                True: ReactiveButtonStateStyle(
                    label="Unmark as watched",
                    style=discord.ButtonStyle.primary,
                    emoji="❌",
                ),
            },
            row=1,
        )
        self.watched_button.callback = self._watched_button_callback

        self.favorite_button = ReactiveButton(
            initial_state=False,  # This should be updated on _initialize
            state_map={
                False: ReactiveButtonStateStyle(
                    label="Favorite",
                    style=discord.ButtonStyle.primary,
                    emoji="⭐",
                ),
                True: ReactiveButtonStateStyle(
                    label="Unfavorite",
                    style=discord.ButtonStyle.secondary,
                    emoji="❌",
                ),
            },
            row=1,
        )
        self.favorite_button.callback = self._favorite_button_callback

    def _add_items(self) -> None:
        """Add all relevant items to the view."""
        self.add_item(self.watched_button)
        self.add_item(self.favorite_button)

    async def _initialize(self) -> None:
        """Initialize the view to reflect the current state of the media.

        This will (likely) perform database lookups and other necessary operations to obtain
        the current state of the media or the user, configuring the internal state accordingly.

        Tasks that need to be performed here:
            - Call `self._add_items()`
            - Set the state of the watched and favorite buttons.

        This method will only be called once.
        """
        self._add_items()
        self.watched_button.set_state(await self.is_watched())
        self.favorite_button.set_state(await self.is_favorite())

    @abstractmethod
    def _get_embed(self) -> discord.Embed:
        """Get the discord embed to be displayed in the message.

        This embed should contain all the relevant information about the media.
        """
        raise NotImplementedError

    async def _refresh(self) -> None:
        """Edit the message to reflect the current state of the view.

        Called whenever the user-facing view needs to be updated.
        """
        if not self.message:
            raise ValueError("View has no message (not yet sent?), can't refresh")

        await self.message.edit(embed=self._get_embed(), view=self)

    @abstractmethod
    async def is_favorite(self) -> bool:
        """Check if the current media is marked as favorite by the user.

        This will perform a database query.
        """
        raise NotImplementedError

    @abstractmethod
    async def set_favorite(self, state: bool) -> None:  # noqa: FBT001
        """Mark or unmark the current media as favorite.

        This will perform a database operation.
        """
        raise NotImplementedError

    @abstractmethod
    async def is_watched(self) -> bool:
        """Check if the current media is marked as watched by the user.

        This will perform a database query.
        """
        raise NotImplementedError

    @abstractmethod
    async def set_watched(self, state: bool) -> None:  # noqa: FBT001
        """Mark or unmark the current media as watched.

        This will perform a database operation.
        """
        raise NotImplementedError

    async def send(self, interaction: discord.Interaction) -> None:
        """Send the view to the user."""
        await self._initialize()
        await interaction.respond(embed=self._get_embed(), view=self)

    async def _watched_button_callback(self, interaction: discord.Interaction) -> None:
        """Callback for when the user clicks on the mark as watched button."""
        await interaction.response.defer()
        cur_state = self.watched_button.state
        await self.set_watched(not cur_state)
        self.watched_button.set_state(not cur_state)

        await self._refresh()

    async def _favorite_button_callback(self, interaction: discord.Interaction) -> None:
        """Callback for when the user clicks on the mark as favorite button."""
        await interaction.response.defer()
        cur_state = self.favorite_button.state
        await self.set_favorite(not cur_state)
        self.favorite_button.set_state(not cur_state)

        await self._refresh()


class DynamicMediaView(MediaView):
    """Base class for dynamic views`that display info about some media (movie/series/episode).

    A dynamic view is one that can change its state after a user interaction.
    For example, a view that displays different episodes based on user selection.
    """

    @abstractmethod
    async def _update_state(self) -> None:
        """Update the internal state to reflect the currently picked media.

        Called whenever the picked media is changed.
        """
        raise NotImplementedError

    @override
    async def _initialize(self) -> None:
        await super()._initialize()
        await self._update_state()

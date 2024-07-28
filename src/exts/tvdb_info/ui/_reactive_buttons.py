from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import discord
from discord.emoji import Emoji
from discord.enums import ButtonStyle
from discord.partial_emoji import PartialEmoji


@dataclass
class ReactiveButtonStateStyle:
    """Style of a reactive button.

    This determines how the button will appear for this state.
    """

    label: str
    style: discord.ButtonStyle
    emoji: str

    def apply(self, button: discord.ui.Button[Any]) -> None:
        """Apply this state to the button."""
        button.label = self.label
        button.style = self.style
        button.emoji = self.emoji


class ReactiveButton[S, V: discord.ui.View](discord.ui.Button[V]):
    """A state-aware button, which can change its appearance based on the state it's in.

    This is very useful to quickly switch between various states of a button, such as "Add" and "Remove".
    """

    @override
    def __init__(
        self,
        *,
        initial_state: S,
        state_map: Mapping[S, ReactiveButtonStateStyle],
        style: ButtonStyle = ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | Emoji | PartialEmoji | None = None,
        sku_id: int | None = None,
        row: int | None = None,
    ):
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            sku_id=sku_id,
            row=row,
        )

        _state = initial_state
        self.state_map = state_map

    @property
    def state(self) -> S:
        """Get the current state of the button."""
        return self._state

    # This is intentionally not a state.setter, as this makes it clerer
    # to the caller that this method changes modifies the button.
    def set_state(self, state: S) -> None:
        """Set the state of the button."""
        self._state = state
        style = self.state_map[state]
        style.apply(self)

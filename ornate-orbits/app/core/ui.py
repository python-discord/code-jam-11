from collections.abc import Sequence
from random import shuffle
from typing import Final
from uuid import UUID

from discord import (
    Client,
    Embed,
    Interaction,
    Member,
    SelectOption,
    User,
)
from discord.app_commands import Command
from discord.ui import Select, View

from app.core.wordle import WordleGame
from app.models.guess import Guess
from app.storage.wordle import wordle_repo
from app.word_generator import Difficulty

EMOJI: Final[list[str]] = [
    ":green_heart:",
    ":yellow_heart:",
    ":blue_heart:",
    ":purple_heart:",
    ":heart:",
]


class GuessEmbed(Embed):
    """Embed that show the guesses of the player."""

    _2_SPACES: Final[str] = "  "
    _4_SPACES: Final[str] = "    "

    def __init__(self, user: User | Member, guesses: Sequence[Guess]) -> None:
        super().__init__(title=f"{user.name}'s Wordle Guess")
        self.color = 0xFF0000 if int(guesses[-1].result) != 0 else 0x00FF00

        for idx, guess in enumerate(guesses):
            self.add_field(
                name=f"Guess #{idx + 1}",
                value=(
                    f"{self._format_guess_word(guess.content)}\n{self._format_guess_result(guess.result)}"
                ),
                inline=False,
            )

    def _format_guess_word(self, word: str) -> str:
        """Format the guess word to show on the embed."""
        new_word = f"{self._2_SPACES}{self._4_SPACES.join(word)}"

        return (
            new_word.replace("L", " L ")
            .replace("J", "  J ")
            .replace("I", "  I ")
        )

    def _format_guess_result(self, word: str) -> str:
        """Format the result into emoji to show on the embed."""
        return " ".join(EMOJI[int(val)] for val in word)


class PlayerStatEmbed(Embed):
    """Embed that show the player stats."""

    def __init__(  # noqa: PLR0913
        self,
        player_id: int,
        player_name: str,
        num_wordle_games: int,
        num_wins: int,
        num_guesses: int,
    ) -> None:
        super().__init__(title=f"{player_name}'s stats")

        self.add_field(
            name="Player ID",
            value=player_id,
            inline=False,
        )

        self.add_field(
            name="Player name",
            value=player_name,
            inline=False,
        )

        self.add_field(
            name="Wordle Games",
            value=num_wordle_games,
            inline=False,
        )

        self.add_field(
            name="Wins",
            value=num_wins,
            inline=False,
        )

        self.add_field(
            name="Guesses",
            value=num_guesses,
            inline=False,
        )

        self.add_field(
            name="Average guesses per game",
            value=num_guesses // num_wordle_games,
            inline=False,
        )


class HelpEmbed(Embed):
    """Embed for the help comment."""

    def __init__(self, commands: list[Command]) -> None:
        super().__init__(title="Command Info")

        for command in commands:
            self.add_field(
                name=f"/{command.name}",
                value=f" :right_arrow: {command.description}",
                inline=False,
            )


class StartSelectionView(View):
    """View that contains all the Select when game start."""

    def __init__(self, *, timeout: float | None = 180) -> None:
        self.length_selected = False
        self.difficulty_selected = False
        super().__init__(timeout=timeout)

        self.length_select = LengthSelect()
        self.difficulty_select = DifficultySelect()

        self.add_item(self.length_select)
        self.add_item(self.difficulty_select)

    async def start(self, interaction: Interaction[Client]) -> None:
        """Start the Wordle Game."""
        await WordleGame().start(
            interaction=interaction,
            length_select=self.length_select,
            difficulty_select=self.difficulty_select,
        )


class LengthSelect(Select[StartSelectionView]):
    """Select that choose the length of a word in a Wordle Game."""

    OPTION_PLACEHOLDER: Final[str] = "Choose Length of Word"
    MIN_VALUES: Final[int] = 1
    MAX_VALUES: Final[int] = 1

    def __init__(self) -> None:
        options = [
            SelectOption(
                label=f"{val} letters",
                value=str(val),
                description=f"The Wordle Game will be a {val} letters word.",
            )
            for val in range(5, 16)
        ]

        super().__init__(
            placeholder=self.OPTION_PLACEHOLDER,
            min_values=self.MIN_VALUES,
            max_values=self.MAX_VALUES,
            options=options,
        )

        self.add_option(
            label="Random",
            value="0",
            description="Choose a random letter word for the Wordle Game.",
        )

    async def callback(self, interaction: Interaction[Client]) -> None:
        """User made a selection."""
        if self.view is None:
            return

        self.view.length_selected = True

        if self.view.length_selected and self.view.difficulty_selected:
            await self.view.start(interaction)
        else:
            await interaction.response.defer()


class DifficultySelect(Select[StartSelectionView]):
    """Select that choose the length of a word in a Wordle Game."""

    OPTION_PLACEHOLDER: Final[str] = "Choose Wordle Game Difficulty"
    MIN_VALUES: Final[int] = 1
    MAX_VALUES: Final[int] = 1

    def __init__(self) -> None:
        options = [
            SelectOption(
                label=val,
                value=val,
                description=f"{val} Mode of Wordle",
                # emoji
            )
            for val in Difficulty
        ]

        super().__init__(
            placeholder=self.OPTION_PLACEHOLDER,
            min_values=self.MIN_VALUES,
            max_values=self.MAX_VALUES,
            options=options,
        )

    async def callback(self, interaction: Interaction[Client]) -> None:
        """User made a selection."""
        if self.view is None:
            return

        self.view.difficulty_selected = True

        if self.view.length_selected and self.view.difficulty_selected:
            await self.view.start(interaction)
        else:
            await interaction.response.defer()


class TrivialSelectionView(View):
    """View that contains all the Select in a trivial question."""

    OPTION_PLACEHOLDER: Final[str] = "Select the correct answer"
    MIN_VALUES: Final[int] = 1
    MAX_VALUES: Final[int] = 1

    CORRECT_VALUE: Final[str] = "0"

    def __init__(
        self,
        correct_answer: str,
        wrong_answers: list[str],
        wordle_id: UUID,
        *,
        timeout: float | None = 180,
    ) -> None:
        self.wordle_id = wordle_id
        super().__init__(timeout=timeout)

        options = [
            SelectOption(
                label=ans,
                value=str(idx),
            )
            for idx, ans in enumerate(wrong_answers, 1)
        ]

        options.append(SelectOption(label=correct_answer, value="0"))

        shuffle(options)

        self.select: Select[TrivialSelectionView] = Select(
            placeholder=self.OPTION_PLACEHOLDER,
            min_values=self.MIN_VALUES,
            max_values=self.MAX_VALUES,
            options=options,
        )

        self.select.callback = self.check_answer  # type: ignore[method-assign]

        self.add_item(self.select)

    async def check_answer(self, interaction: Interaction[Client]) -> None:
        """Check if the selection is same as the answer."""
        if self.select.values[0] != self.CORRECT_VALUE:  # noqa: PD011
            await interaction.response.send_message("Wrong Answer")
            await wordle_repo.change_status(
                id=self.wordle_id, is_winning=False
            )
            return

        await interaction.response.send_message("Correct Answer")
        await wordle_repo.change_status(id=self.wordle_id, is_winning=False)

        wordle_game = WordleGame()
        wordle = await wordle_repo.get_ongoing_wordle(
            user_id=interaction.user.id
        )
        await interaction.followup.send("Incoming hint ...")

        hint = await wordle_game.get_hint(
            user_id=interaction.user.id, word=wordle.word
        )
        await interaction.followup.send(hint)

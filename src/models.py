from collections.abc import Callable
from typing import Any, Literal, get_args

from attrs import asdict, field, frozen
from interactions import ActionRow, Button, ButtonStyle, Embed

from game import PlayerState, Stage

Consequence = dict[Any, Any]
Condition = Callable[[PlayerState], bool] | None


def always_true(_: PlayerState) -> Literal[True]:
    """Return True."""
    return True


@frozen
class Template:
    """Make a template for the messages to be served."""

    text: str
    choices: dict[str, Consequence]  # Specify button color here somehow.
    condition: Condition | None = field(converter=lambda condition: always_true if condition is None else condition)

    def format(self, state: PlayerState) -> str:
        """Format the text."""
        return self.text.format(asdict(state))

    def to_embed(self, state: PlayerState) -> tuple[Embed, ActionRow]:
        """Return embed and action row for UI."""
        buttons: list[Button] = []

        for id, choice in enumerate(self.choices.items()):
            button = Button(
                label=f"{next(iter(choice.keys()))}",  # Something isn't right here
                style=ButtonStyle.BLURPLE,
                custom_id=f"Choice {id}",
            )
            buttons.append(button)

        action_row = ActionRow(*buttons)

        embed = Embed(
            title=state.nation_name,
            description=self.text,
            color=(0, 0, 255),
            # Can we access Actor here in this class? like this actor is saying this
            # hazyfossa: good question
        )
        return (embed, action_row)


TotalStages = get_args(Stage)


@frozen
class StageGroup:
    """A helper class to group templates based on their stage in game."""

    stage: Stage | tuple[Stage] | Literal["all"] = field(
        converter=lambda stage: TotalStages if stage == "all" else stage,
    )
    templates: list[Template]


@frozen
class Actor:
    """An in-game character."""

    name: str
    picture: str  # we'll need to serve these as static content probably
    templates: list[StageGroup]

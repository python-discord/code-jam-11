import sys
import textwrap
from typing import Self, override

import discord
from discord.interactions import Interaction
from discord.ui import Item

from src.exts.error_handler.utils import build_error_embed
from src.settings import GITHUB_REPO
from src.utils.log import get_logger

log = get_logger(__name__)


# TODO: Is this file really the right place for this? Or would utils work better?
class ErrorHandledView(discord.ui.View):
    """View with error-handling support."""

    @override
    async def on_error(self, error: Exception, item: Item[Self], interaction: Interaction) -> None:
        log.exception(
            f"Unhandled exception in view: {self.__class__.__name__} (item={item.__class__.__name__})",
            exc_info=True,
        )

        exc_info = sys.exc_info()
        exc = exc_info[1]
        if exc is None:
            await super().on_error(error, item, interaction)
            return

        embed = build_error_embed(
            title="Unhandled exception",
            description=textwrap.dedent(
                f"""
                Unknown error has occurred without being properly handled.
                Please report this at the [GitHub repository]({GITHUB_REPO})

                **View**: `{self.__class__.__name__}`
                **Item**: `{item.__class__.__name__}`
                **Exception details**: ```{exc.__class__.__name__}: {exc}```
                """
            ),
        )
        if interaction.user is not None:
            msg = f"Sorry {interaction.user.mention}"
        else:
            msg = ""

        await interaction.respond(msg, embed=embed)

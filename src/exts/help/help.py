from typing import Any

import discord
from discord import (
    ApplicationCommand,
    ApplicationContext,
    CheckFailure,
    Cog,
    SlashCommand,
    SlashCommandGroup,
    slash_command,
)
from discord.ext.commands import CheckFailure as CommandCheckFailure
from discord.ext.pages import Page, Paginator

from src.bot import Bot
from src.settings import COMMAND_EMOJI, GROUP_EMOJI
from src.utils import mention_command
from src.utils.cat_api import get_cat_image_url
from src.utils.log import get_logger

log = get_logger(__name__)


class HelpCog(Cog):
    """Cog to provide help info for all available bot commands."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command()
    async def help(self, ctx: ApplicationContext) -> None:
        """Shows help for all available commands."""
        cat_image_url: str = await get_cat_image_url(self.bot.http_session)
        fields: list[tuple[str, str]] = []

        async def gather_all_commands(command: ApplicationCommand[Any, ..., Any], depth: int = 0) -> None:
            try:
                can_run = await command.can_run(ctx)
            except (CheckFailure, CommandCheckFailure):
                can_run = False
            if not can_run:
                return
            full_command_name: str = f"{mention_command(command)}".strip()
            if isinstance(command, SlashCommand):
                fields.append(
                    (f'{COMMAND_EMOJI} {full_command_name} {"sub-" * (depth-1)}command', f"{command.description}")
                )
            elif isinstance(command, SlashCommandGroup):
                fields.append((f'{GROUP_EMOJI}`{command}` {"sub-" * depth}group', f"{command.description}"))
                for subcommand in command.subcommands:
                    await gather_all_commands(subcommand, depth + 1)
            else:
                log.error(f"Got unexpected command type: {command.__class__.__name__}, {command!r}")

        for command in self.bot.commands:
            await gather_all_commands(command)

        new_embed = lambda url: discord.Embed(title="Help command").set_thumbnail(url=url)

        embeds: list[discord.Embed] = [new_embed(cat_image_url)]
        for name, value in fields:
            if len(embeds[-1].fields) >= 5:
                embeds.append(new_embed(cat_image_url))
            embeds[-1].add_field(name=name, value=value, inline=False)
        paginator = Paginator([Page(embeds=[embed]) for embed in embeds])
        await paginator.respond(ctx.interaction)


def setup(bot: Bot) -> None:
    """Register the HelpCog cog."""
    bot.add_cog(HelpCog(bot))

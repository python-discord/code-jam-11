from typing import cast, override

from discord import (
    ApplicationContext,
    Bot,
    Cog,
    ExtensionAlreadyLoaded,
    ExtensionNotLoaded,
    SlashCommandGroup,
    User,
    option,
)
from discord.ext.commands.errors import NotOwner

from src.converters.bot_extension import ValidBotExtension
from src.settings import FAIL_EMOJI, SUCCESS_EMOJI


class Sudo(Cog):
    """Cog that allows the bot owner to perform various privileged actions."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    sudo = SlashCommandGroup(name="sudo", description="Commands for the bot owner.")

    @sudo.command()
    @option("extension", ValidBotExtension)
    async def load(self, ctx: ApplicationContext, extension: str) -> None:
        """Dynamically load a requested bot extension.

        This can be very useful for debugging and testing new features without having to restart the bot.
        """
        try:
            self.bot.load_extension(extension)
        except ExtensionAlreadyLoaded:
            await ctx.respond(f"{FAIL_EMOJI} Extension is already loaded")
            return
        await ctx.respond(f"{SUCCESS_EMOJI} Extension `{extension}` loaded")

    @sudo.command()
    @option("extension", ValidBotExtension)
    async def unload(self, ctx: ApplicationContext, extension: str) -> None:
        """Dynamically unload a requested bot extension.

        This can be very useful for debugging and testing new features without having to restart the bot.
        """
        try:
            self.bot.unload_extension(extension)
        except ExtensionNotLoaded:
            await ctx.respond(f"{FAIL_EMOJI} Extension is not loaded")
            return
        await ctx.respond(f"{SUCCESS_EMOJI} Extension `{extension}` unloaded")

    @sudo.command()
    @option("extension", ValidBotExtension)
    async def reload(self, ctx: ApplicationContext, extension: str) -> None:
        """Dynamically reload a requested bot extension.

        This can be very useful for debugging and testing new features without having to restart the bot.
        """
        try:
            self.bot.unload_extension(extension)
        except ExtensionNotLoaded:
            already_loaded = False
        else:
            already_loaded = True
        self.bot.load_extension(extension)

        action = "reloaded" if already_loaded else "loaded"
        await ctx.respond(f"{SUCCESS_EMOJI} Extension `{extension}` {action}")

    @override
    async def cog_check(self, ctx: ApplicationContext) -> bool:
        """Only the bot owners can use this cog."""
        if not await self.bot.is_owner(cast(User, ctx.author)):
            raise NotOwner

        return super().cog_check(ctx)


def setup(bot: Bot) -> None:
    """Load the Reloader cog."""
    bot.add_cog(Sudo(bot))

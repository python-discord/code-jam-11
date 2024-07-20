from discord import ApplicationContext, Bot, CheckFailure, Cog, Embed, SlashCommand, SlashCommandGroup, slash_command
from discord.ext.commands import CheckFailure as CommandCheckFailure

from src.utils import get_cat_image_url, mention_command
from src.utils.log import get_logger

log = get_logger(__name__)


class HelpCog(Cog):
    """Cog to provide help info for all available bot commands."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command()
    async def help(self, ctx: ApplicationContext) -> None:
        """Shows help for all available commands."""
        embed = Embed(
            title="Help command",
            image=await get_cat_image_url(),
        )
        for command in self.bot.commands:
            try:
                can_run = await command.can_run(ctx)
            except (CheckFailure, CommandCheckFailure):
                can_run = False
            if not can_run:
                continue

            if isinstance(command, SlashCommand):
                embed.add_field(name=mention_command(command), value=command.description, inline=False)
            if isinstance(command, SlashCommandGroup):
                embed.add_field(
                    name=f"{mention_command(command)} group",
                    value=command.description
                    + "\n\n"
                    + "\n".join(
                        f"{mention_command(subcommand)}: {subcommand.description}"
                        for subcommand in command.subcommands
                    ),
                    inline=False,
                )
            embed.add_field(name="", value="")
        await ctx.respond(embed=embed)


def setup(bot: Bot) -> None:
    """Register the HelpCog cog."""
    bot.add_cog(HelpCog(bot))

import textwrap
from typing import cast

from discord import Any, ApplicationContext, Cog, Colour, Embed, EmbedField, EmbedFooter, errors
from discord.ext.commands import errors as commands_errors

from src.bot import Bot
from src.settings import FAIL_EMOJI, GITHUB_REPO
from src.utils.log import get_logger
from src.utils.ratelimit import RateLimitExceededError

log = get_logger(__name__)


class ErrorHandler(Cog):
    """Cog to handle any errors invoked from commands."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_error_embed(
        self,
        ctx: ApplicationContext,
        *,
        title: str | None = None,
        description: str | None = None,
        fields: list[EmbedField] | None = None,
        footer: EmbedFooter | None = None,
    ) -> None:
        """Send an embed regarding the unhandled exception that occurred."""
        if title is None and description is None:
            raise ValueError("You need to provide either a title or a description.")

        embed = Embed(
            title=title,
            description=description,
            color=Colour.red(),
            fields=fields,
            footer=footer,
        )
        await ctx.respond(f"Sorry, {ctx.author.mention}", embed=embed)

    async def send_unhandled_embed(self, ctx: ApplicationContext, exc: BaseException) -> None:
        """Send an embed regarding the unhandled exception that occurred."""
        msg = f"Exception {exc!r} has occurred from command {ctx.command.qualified_name} invoked by {ctx.author.id}"
        if ctx.message:
            msg += f" in message {ctx.message.content!r}"
        if ctx.guild:
            msg += f" on guild {ctx.guild.id}"
        log.warning(msg)

        await self.send_error_embed(
            ctx,
            title="Unhandled exception",
            description=textwrap.dedent(
                f"""
                Unknown error has occurred without being properly handled.
                Please report this at the [GitHub repository]({GITHUB_REPO})

                **Command**: `{ctx.command.qualified_name}`
                **Exception details**: ```{exc.__class__.__name__}: {exc}```
                """
            ),
        )

    async def _handle_check_failure(
        self,
        ctx: ApplicationContext,
        exc: errors.CheckFailure | commands_errors.CheckFailure,
    ) -> None:
        if isinstance(exc, commands_errors.CheckAnyFailure):
            # We don't really care that all of the checks have failed, we need to produce an error message here,
            # so just take the first failure and work with that as the error.

            # Even though the docstring says that exc.errors should contain the CheckFailure exceptions,
            # the type-hint says that the errors should be in exc.checks... Cast the type away to Any
            # and just check both, see where the error actually is and use that
            errors1 = cast(list[Any], exc.errors)
            errors2 = cast(list[Any], exc.checks)

            if len(errors1) > 0 and isinstance(errors1[0], (errors.CheckFailure, commands_errors.CheckFailure)):
                exc = errors1[0]
            elif len(errors2) > 0 and isinstance(errors2[0], (errors.CheckFailure, commands_errors.CheckFailure)):
                exc = errors2[0]
            else:
                # Just in case, this library is a mess...
                raise ValueError("Never (hopefully), here's some random code: 0xd1ff0aaac")

        if isinstance(exc, commands_errors.NotOwner):
            await self.send_error_embed(
                ctx,
                description=f"{FAIL_EMOJI} This command is limited to the bot owner.",
            )
            return

        if isinstance(
            exc,
            (
                commands_errors.MissingPermissions,
                commands_errors.MissingRole,
                commands_errors.MissingAnyRole,
            ),
        ):
            await self.send_error_embed(
                ctx,
                description=f"{FAIL_EMOJI} You don't have permission to run this command.",
            )
            return

        if isinstance(
            exc,
            (
                commands_errors.BotMissingRole,
                commands_errors.BotMissingAnyRole,
                commands_errors.BotMissingPermissions,
            ),
        ):
            await self.send_error_embed(
                ctx,
                description=f"{FAIL_EMOJI} I don't have the necessary permissions to perform this action.",
            )

        if isinstance(exc, commands_errors.NoPrivateMessage):
            await self.send_error_embed(ctx, description=f"{FAIL_EMOJI} This command can only be used in a server.")
            return

        if isinstance(exc, commands_errors.PrivateMessageOnly):
            await self.send_error_embed(ctx, description=f"{FAIL_EMOJI} This command can only be used in a DM.")
            return

        if isinstance(exc, commands_errors.NSFWChannelRequired):
            await self.send_error_embed(
                ctx,
                description=f"{FAIL_EMOJI} This command can only be used in an NSFW channel.",
            )
            return

        await self.send_unhandled_embed(ctx, exc)

    async def _handle_command_invoke_error(
        self,
        ctx: ApplicationContext,
        exc: errors.ApplicationCommandInvokeError,
    ) -> None:
        original_exception = exc.__cause__

        if original_exception is None:
            await self.send_unhandled_embed(ctx, exc)
            log.exception("Got ApplicationCommandInvokeError without a cause.", exc_info=exc)
            return

        if isinstance(original_exception, RateLimitExceededError):
            msg = original_exception.msg or "Hit a rate-limit, please try again later."
            time_remaining = f"Expected reset: <t:{round(original_exception.closest_expiration)}:R>"
            footer = None
            if original_exception.updates_when_exceeded:
                footer = EmbedFooter(
                    text="Spamming the command will only increase the time you have to wait.",
                )
            await self.send_error_embed(
                ctx,
                title="Rate limit exceeded",
                description=f"{FAIL_EMOJI} {msg}",
                fields=[EmbedField(name="", value=time_remaining)],
                footer=footer,
            )
            return

        await self.send_unhandled_embed(ctx, original_exception)
        log.exception("Unhandled exception occurred.", exc_info=original_exception)

    @Cog.listener()
    async def on_application_command_error(self, ctx: ApplicationContext, exc: errors.DiscordException) -> None:
        """Handle exceptions that have occurred while running some command."""
        if isinstance(exc, (errors.CheckFailure, commands_errors.CheckFailure)):
            await self._handle_check_failure(ctx, exc)
            return

        if isinstance(exc, errors.ApplicationCommandInvokeError):
            await self._handle_command_invoke_error(ctx, exc)
            return

        await self.send_unhandled_embed(ctx, exc)


def setup(bot: Bot) -> None:
    """Register the ErrorHandler cog."""
    bot.add_cog(ErrorHandler(bot))

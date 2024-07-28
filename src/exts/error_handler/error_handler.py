import sys
from itertools import chain
from typing import cast

from discord import Any, ApplicationContext, Cog, EmbedField, EmbedFooter, errors
from discord.ext.commands import errors as commands_errors

from src.bot import Bot
from src.settings import FAIL_EMOJI
from src.utils.log import get_logger
from src.utils.ratelimit import RateLimitExceededError

from .utils import build_error_embed, build_unhandled_application_embed

log = get_logger(__name__)


class ErrorHandler(Cog):
    """Cog to handle any errors invoked from commands."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

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
            embed = build_error_embed(description=f"{FAIL_EMOJI} This command is limited to the bot owner.")

        elif isinstance(
            exc,
            (
                commands_errors.MissingPermissions,
                commands_errors.MissingRole,
                commands_errors.MissingAnyRole,
            ),
        ):
            embed = build_error_embed(description=f"{FAIL_EMOJI} You don't have permission to run this command.")

        elif isinstance(
            exc,
            (
                commands_errors.BotMissingRole,
                commands_errors.BotMissingAnyRole,
                commands_errors.BotMissingPermissions,
            ),
        ):
            embed = build_error_embed(
                description=f"{FAIL_EMOJI} I don't have the necessary permissions to perform this action."
            )

        elif isinstance(exc, commands_errors.NoPrivateMessage):
            embed = build_error_embed(description=f"{FAIL_EMOJI} This command can only be used in a server.")

        elif isinstance(exc, commands_errors.PrivateMessageOnly):
            embed = build_error_embed(description=f"{FAIL_EMOJI} This command can only be used in a DM.")

        elif isinstance(exc, commands_errors.NSFWChannelRequired):
            embed = build_error_embed(description=f"{FAIL_EMOJI} This command can only be used in an NSFW channel.")
        else:
            embed = build_unhandled_application_embed(ctx, exc)

        await ctx.send(f"Sorry {ctx.author.mention}", embed=embed)

    async def _handle_command_invoke_error(
        self,
        ctx: ApplicationContext,
        exc: errors.ApplicationCommandInvokeError,
    ) -> None:
        original_exception = exc.__cause__

        if original_exception is None:
            embed = build_unhandled_application_embed(ctx, exc)
            log.exception("Got ApplicationCommandInvokeError without a cause.", exc_info=exc)

        elif isinstance(original_exception, RateLimitExceededError):
            msg = original_exception.msg or "Hit a rate-limit, please try again later."
            time_remaining = f"Expected reset: <t:{round(original_exception.closest_expiration)}:R>"
            footer = None
            if original_exception.updates_when_exceeded:
                footer = EmbedFooter(
                    text="Spamming the command will only increase the time you have to wait.",
                )
            embed = build_error_embed(
                title="Rate limit exceeded",
                description=f"{FAIL_EMOJI} {msg}",
                fields=[EmbedField(name="", value=time_remaining)],
                footer=footer,
            )
        else:
            embed = build_unhandled_application_embed(ctx, original_exception)
            log.exception("Unhandled exception occurred.", exc_info=original_exception)

        await ctx.send(f"Sorry {ctx.author.mention}", embed=embed)

    @Cog.listener()
    async def on_application_command_error(self, ctx: ApplicationContext, exc: errors.DiscordException) -> None:
        """Handle exceptions that have occurred while running some command."""
        if isinstance(exc, (errors.CheckFailure, commands_errors.CheckFailure)):
            await self._handle_check_failure(ctx, exc)
            return

        if isinstance(exc, errors.ApplicationCommandInvokeError):
            await self._handle_command_invoke_error(ctx, exc)
            return

        embed = build_unhandled_application_embed(ctx, exc)
        await ctx.send(f"Sorry {ctx.author.mention}", embed=embed)

    @Cog.listener()
    async def on_error(self, event_method: str, *args: object, **kwargs: object) -> None:
        """Handle exception that have occurred in any event.

        This is a catch-all for errors that aren't handled by any other listeners, or fell through (were re-raised).
        """
        log.exception(f"Unhandled excepton occurred {event_method=} {args=!r} {kwargs=!r}", exc_info=True)

        exc = sys.exc_info()[1]
        if exc is None:
            return

        for arg in chain(args, kwargs.values()):
            if isinstance(arg, ApplicationContext):
                ctx = arg

                embed = build_unhandled_application_embed(ctx, exc)
                await ctx.send(f"Sorry {ctx.author.mention}", embed=embed)
                return


def setup(bot: Bot) -> None:
    """Register the ErrorHandler cog."""
    bot.add_cog(ErrorHandler(bot))

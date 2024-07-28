import textwrap

from discord import ApplicationContext, Colour, Embed, EmbedField, EmbedFooter

from src.settings import GITHUB_REPO
from src.utils.log import get_logger

log = get_logger(__name__)


def build_error_embed(
    *,
    title: str | None = None,
    description: str | None = None,
    fields: list[EmbedField] | None = None,
    footer: EmbedFooter | None = None,
) -> Embed:
    """Create an embed regarding the unhandled exception that occurred."""
    if title is None and description is None:
        raise ValueError("You need to provide either a title or a description.")

    return Embed(
        title=title,
        description=description,
        color=Colour.red(),
        fields=fields,
        footer=footer,
    )


def build_unhandled_application_embed(ctx: ApplicationContext, exc: BaseException) -> Embed:
    """Build an embed regarding the unhandled exception that occurred."""
    msg = f"Exception {exc!r} has occurred from command {ctx.command.qualified_name} invoked by {ctx.author.id}"
    if ctx.message:
        msg += f" in message {ctx.message.content!r}"
    if ctx.guild:
        msg += f" on guild {ctx.guild.id}"
    log.warning(msg)

    return build_error_embed(
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


async def send_unhandled_application_embed(ctx: ApplicationContext, exc: BaseException) -> None:
    """Send an embed regarding the unhandled exception that occurred."""
    await ctx.send(f"Sorry {ctx.author.mention}", embed=build_unhandled_application_embed(ctx, exc))

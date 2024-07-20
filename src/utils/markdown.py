from typing import Any

import discord


def mention_command(command: discord.ApplicationCommand[Any, ..., Any], bot: discord.Bot) -> str:
    """Mentions the command using discord markdown."""
    return f"</{command.qualified_name}:{command.qualified_id}>"

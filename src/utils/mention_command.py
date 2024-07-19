import discord


def mention_command(command: str, bot: discord.Bot) -> str:
    """Mentions the command."""
    discord_command = bot.get_command(command)
    if not discord_command:
        raise ValueError("command not found")
    return f"</{command}:{discord_command.qualified_id}>"

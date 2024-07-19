import os
from typing import Final


class BotSettings:
    """All settings for the Bot application goes here."""

    COMMAND_PREFIX: Final[str] = os.getenv("COMMAND_PREFIX", "!@#")
    DISCORD_TOKEN: Final[str] = os.environ["DISCORD_TOKEN"]
    GUILD_ID: Final[str] = os.environ["GUILD_ID"]


settings = BotSettings()

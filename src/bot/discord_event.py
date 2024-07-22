from dataclasses import dataclass
from datetime import datetime

import discord


@dataclass
class FakeUser:
    """A class representing a fake user for testing or placeholder purposes.

    Attributes
    ----------
        id (int): The unique identifier for the fake user.
        display_name (str): The display name of the fake user.

    """

    id: int
    display_name: str


@dataclass
class DiscordEvent:
    """A class representing a Discord event with relevant information.

    Attributes
    ----------
        type (str): The type of the Discord event.
        timestamp (datetime): The timestamp when the event occurred.
        guild (discord.Guild): The Discord guild (server) where the event took place.
        channel (discord.TextChannel): The specific text channel where the event occurred.
        user (discord.User | FakeUser): The user who triggered the event, either a Discord user or a FakeUser.
        content (str): The content or message associated with the event.

    """

    type: str
    timestamp: datetime
    guild: discord.Guild
    channel: discord.TextChannel
    user: discord.User | FakeUser
    content: str

from dataclasses import dataclass
from datetime import datetime

import discord


@dataclass
class FakeUser:
    id: int
    display_name: str


@dataclass
class DiscordEvent:
    type: str
    timestamp: datetime
    guild: discord.Guild
    channel: discord.TextChannel
    user: discord.User | FakeUser
    content: str

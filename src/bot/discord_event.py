from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
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
class SerializableGuild:
    """Serializable representation of a Discord guild.

    Attributes
    ----------
        id (int): The unique identifier of the guild.
        name (str): The name of the guild.
        verification_level (int): The verification level of the guild.

    """

    id: int
    name: str
    verification_level: int


@dataclass
class SerializableTextChannel:
    """Serializable representation of a Discord text channel.

    Attributes
    ----------
        id (int): The unique identifier of the text channel.
        name (str): The name of the text channel.

    """

    id: int
    name: str


@dataclass
class SerializableUser:
    """Serializable representation of a Discord user.

    Attributes
    ----------
        id (int): The unique identifier of the user.
        name (str): The username of the user.
        display_name (str): The display name of the user.

    """

    id: int
    name: str
    display_name: str


@dataclass
class DiscordEvent:
    """A class representing a Discord event with relevant information.

    Attributes
    ----------
        type (str): The type of the Discord event.
        timestamp (datetime): The timestamp when the event occurred.
        guild (SerializableGuild): Serializable representation of the Discord guild.
        channel (SerializableTextChannel): Serializable representation of the text channel.
        user (SerializableUser | FakeUser): Serializable representation of the user or a FakeUser.
        content (str): The content or message associated with the event.

    """

    type: str
    timestamp: datetime
    guild: SerializableGuild
    channel: SerializableTextChannel
    user: SerializableUser | FakeUser
    content: str

    @classmethod
    def from_discord_objects(
        cls,
        type: str,
        timestamp: datetime,
        guild: Optional["discord.Guild"],
        channel: Optional["discord.TextChannel"],
        user: Optional["discord.User"],
        content: str,
    ) -> "DiscordEvent":
        return cls(
            type=type,
            timestamp=timestamp,
            guild=SerializableGuild(guild.id, guild.name, guild.verification_level.value) if guild else None,
            channel=SerializableTextChannel(channel.id, channel.name) if channel else None,
            user=SerializableUser(user.id, user.name, user.display_name) if user else None,
            content=content,
        )

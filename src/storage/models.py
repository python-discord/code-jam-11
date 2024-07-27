import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import aiosqlite

from bot.discord_event import DiscordEvent


@dataclass
class DBEvent:
    """Represents a database event."""

    event_type: str
    timestamp: int
    guild_id: int
    channel_id: int
    member_id: int
    message_id: int | None
    content: str | None


class EventTypeEnum(str, Enum):
    """Enum for event types."""

    MESSAGE = "message"
    TYPING = "typing"
    REACTION = "reaction"


class CommandType(str, Enum):
    """Enum for command types."""

    ON_LOAD = "on_load"
    GET = "get"
    INSERT = "insert"


@dataclass
class GuildConfig:
    """Represents guild configuration."""

    guild_id: int
    allowed_channels: list[int]
    gif_channel: int | None


class Database:
    """Handles database operations."""

    def __init__(self, db_name: str) -> None:
        """Initialize the Database.

        Args:
        ----
            db_name (str): The name of the database.

        """
        self.db_file_path = f"{db_name}.sqlite3"

    async def initialize(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        if not Path(self.db_file_path).exists():
            async with aiosqlite.connect(self.db_file_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id TEXT NOT NULL PRIMARY KEY,
                        guild_id INT NOT NULL,
                        event_type TEXT NOT NULL,
                        timestamp INT NOT NULL,
                        channel_id INT NOT NULL,
                        member_id INT NOT NULL,
                        message_id TEXT,
                        content TEXT
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_config (
                        guild_id INTEGER PRIMARY KEY,
                        allowed_channels TEXT NOT NULL,
                        gif_channel INTEGER
                    )
                """)
                await db.commit()
        print("Database initialized successfully.")

    async def execute(self, command: CommandType, query: str | None = None, parameters: tuple | None = None) -> None:
        """Execute a database command.

        Args:
        ----
            command (CommandType): The type of command to execute.
            query (Optional[str], optional): The SQL query. Defaults to None.
            parameters (Optional[tuple], optional): Query parameters. Defaults to None.

        """
        async with aiosqlite.connect(self.db_file_path) as db:
            cursor = await db.cursor()
            match command:
                case CommandType.ON_LOAD:
                    try:
                        await cursor.execute(query)
                        await db.commit()
                    except aiosqlite.DatabaseError as e:
                        print(f"DB ONLOAD ERROR: {e}")
                    print("database loaded successfully.")
                case CommandType.INSERT:
                    try:
                        await cursor.execute(query, parameters)
                        await db.commit()
                    except aiosqlite.DatabaseError as e:
                        print(f"DB INSERT ERROR: {e}")
                    print("database insert successfully.")
                case CommandType.GET:
                    try:
                        await db.execute_fetchall(query, parameters)
                    except aiosqlite.DatabaseError as e:
                        print(f"DB READ ERROR: {e}")

    async def insert_event(self, event: DBEvent) -> None:
        query = """
        INSERT INTO events(id, guild_id, event_type, timestamp, channel_id, member_id, message_id, content)
        VALUES(?,?,?,?,?,?,?,?)
        """
        data = (
            str(uuid.uuid4()),
            event.guild_id,
            event.event_type,
            event.timestamp,
            event.channel_id,
            event.member_id,
            event.message_id,
            event.content,
        )
        await self.execute(command=CommandType.INSERT, query=query, parameters=data)

    async def get_events_by_guild(self, guild_id: int, start_time: int, stop_time: int) -> list[DBEvent]:
        """Retrieve events for a specific guild within a specified time range.

        Args:
        ----
            guild_id (int): The ID of the guild.
            start_time (int): The start timestamp.
            stop_time (int): The end timestamp.

        Returns:
        -------
            list[DBEvent]: A list of DBEvent objects.

        """
        query = """
        SELECT event_type, timestamp, guild_id, channel_id, member_id, message_id, content
        FROM events
        WHERE guild_id = ? AND timestamp BETWEEN ? AND ?
        """
        async with aiosqlite.connect(self.db_file_path) as db:
            cursor = await db.execute(query, (guild_id, start_time, stop_time))
            rows = await cursor.fetchall()
            return [DBEvent(*row) for row in rows]

    async def set_guild_config(self, config: GuildConfig) -> None:
        """Set or update the configuration for a guild."""
        query = """
        INSERT OR REPLACE INTO guild_config (guild_id, allowed_channels, gif_channel)
        VALUES (?, ?, ?)
        """
        allowed_channels_str = ",".join(map(str, config.allowed_channels))
        data = (config.guild_id, allowed_channels_str, config.gif_channel)
        await self.execute(command=CommandType.INSERT, query=query, parameters=data)

    async def get_guild_config(self, guild_id: int) -> GuildConfig | None:
        """Retrieve the configuration for a specific guild."""
        query = """
        SELECT guild_id, allowed_channels, gif_channel
        FROM guild_config
        WHERE guild_id = ?
        """
        async with aiosqlite.connect(self.db_file_path) as db:
            cursor = await db.execute(query, (guild_id,))
            row = await cursor.fetchone()
            if row:
                guild_id, allowed_channels_str, gif_channel = row
                allowed_channels = list(map(int, allowed_channels_str.split(",")))
                return GuildConfig(guild_id, allowed_channels, gif_channel)
            return None


async def event_db_builder(event: DiscordEvent) -> DBEvent:
    """Build a DBEvent from a DiscordEvent.

    Args:
    ----
        event (DiscordEvent): The Discord event to convert.

    Returns:
    -------
        DBEvent: The converted database event.

    """
    message_id = event.message.id if event.type in {EventTypeEnum.MESSAGE, EventTypeEnum.REACTION} else None
    return DBEvent(
        event_type=event.type,
        timestamp=event.timestamp.timestamp().__round__(),
        guild_id=event.guild.id,
        channel_id=event.channel.id,
        member_id=event.user.id,
        message_id=message_id,
        content=event.content,
    )

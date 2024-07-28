import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

import aiosqlite


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


@dataclass
class UserInfo:
    """Represents user information.

    Attributes
    ----------
    user_id : int
        The unique identifier for the user.
    guild_id : int
        The unique identifier for the guild the user belongs to.
    avatar_data : bytes | None
        The binary data of the user's avatar image, if available.
    role_color : int | None
        The color associated with the user's role, if any.
    last_updated : datetime
        The timestamp of when the user information was last updated.

    """

    user_id: int
    guild_id: int
    avatar_data: bytes | None
    role_color: int | None
    last_updated: datetime


class Database:
    """Handles database operations."""

    def __init__(self, db_name: str) -> None:
        """Initialize the Database.

        Args:
        ----
            db_name (str): The name of the database.

        """
        self.db_file_path = f"{db_name}.sqlite3"
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        try:
            async with aiosqlite.connect(self.db_file_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_config (
                        guild_id INTEGER PRIMARY KEY,
                        allowed_channels TEXT NOT NULL,
                        gif_channel INTEGER
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_info (
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER NOT NULL,
                        avatar_data BLOB,
                        role_color TEXT,
                        last_updated TIMESTAMP NOT NULL,
                        PRIMARY KEY (user_id, guild_id)
                    )
                """)
                await db.commit()
            self.logger.info("Database initialized successfully.")
        except aiosqlite.Error:
            self.logger.exception("Failed to initialize database")
            raise

    async def execute(self, command: CommandType, query: str | None = None, parameters: tuple | None = None) -> None:
        """Execute a database command.

        Args:
        ----
            command (CommandType): The type of command to execute.
            query (Optional[str], optional): The SQL query. Defaults to None.
            parameters (Optional[tuple], optional): Query parameters. Defaults to None.

        Raises:
        ------
            aiosqlite.Error: If there's an error executing the database command.

        """
        try:
            async with aiosqlite.connect(self.db_file_path) as db:
                db: aiosqlite.Connection
                cursor = await db.cursor()
                match command:
                    case CommandType.ON_LOAD:
                        await cursor.execute(query)
                        await db.commit()
                        self.logger.info("Database loaded successfully.")
                    case CommandType.INSERT:
                        await cursor.execute(query, parameters)
                        await db.commit()
                    case CommandType.GET:
                        return await db.execute_fetchall(query, parameters)
        except aiosqlite.Error:
            self.logger.exception("Database error (%s)", command.value)
            raise

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
        async with aiosqlite.connect(self.db_file_path) as db, db.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                guild_id, allowed_channels_str, gif_channel = row
                allowed_channels = list(map(int, allowed_channels_str.split(",")))
                return GuildConfig(guild_id, allowed_channels, gif_channel)
            return None

    async def get_user_info(self, user_id: int, guild_id: int) -> UserInfo | None:
        """Retrieve user info for a specific user in a specific guild."""
        query = """
        SELECT user_id, guild_id, avatar_data, role_color, last_updated
        FROM user_info
        WHERE user_id = ? AND guild_id = ?
        """
        async with aiosqlite.connect(self.db_file_path) as db, db.execute(query, (user_id, guild_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserInfo(
                    user_id=row[0],
                    guild_id=row[1],
                    avatar_data=row[2],
                    role_color=row[3],
                    last_updated=datetime.fromisoformat(row[4]).replace(tzinfo=UTC),
                )
            return None

    async def set_user_info(self, user_info: UserInfo) -> None:
        """Set or update the user info for a specific user in a specific guild."""
        query = """
        INSERT OR REPLACE INTO user_info (user_id, guild_id, avatar_data, role_color, last_updated)
        VALUES (?, ?, ?, ?, ?)
        """
        data = (
            user_info.user_id,
            user_info.guild_id,
            user_info.avatar_data,
            user_info.role_color,
            user_info.last_updated.isoformat(),
        )
        await self.execute(command=CommandType.INSERT, query=query, parameters=data)

    async def get_random_user_info(self) -> UserInfo | None:
        """Retrieve random user info for a specific guild."""
        query = """
        SELECT user_id, guild_id, avatar_data, role_color, last_updated
        FROM user_info
        ORDER BY RANDOM()
        LIMIT 1
        """
        async with aiosqlite.connect(self.db_file_path) as db, db.execute(query) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserInfo(
                    user_id=row[0],
                    guild_id=row[1],
                    avatar_data=row[2],
                    role_color=row[3],
                    last_updated=datetime.fromisoformat(row[4]),
                )
            return None

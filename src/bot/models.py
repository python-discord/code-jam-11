import uuid
from dataclasses import dataclass
from enum import Enum

import aiosqlite

from bot.discord_event import DiscordEvent
from bot.settings import db_path


@dataclass
class DBEvent:
    event_type: str
    timestamp: int
    guild_id: int
    channel_id: int
    member_id: int
    message_id: int | None
    content: str | None


class EventTypeEnum(str, Enum):
    MESSAGE = "message"
    TYPING = "typing"
    REACTION = "reaction"


class CommandType(str, Enum):
    ON_LOAD = "on_load"
    GET = "get"
    INSERT = "insert"


class EventsDatabase:
    def __init__(self, guild_name: str):
        self.db_name = guild_name + "_events.db"
        self.db_file_path = str(db_path / self.db_name)

    async def execute(self, command: CommandType, query: str = None, parameters: tuple = None):
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

    async def load_table(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS events (
        id TEXT NOT NULL PRIMARY KEY,
        event_type TEXT NOT NULL,
        timestamp INT NOT NULL,
        guild_id INT NOT NULL,
        channel_id INT NOT NULL,
        member_id INT NOT NULL,
        message_id TEXT,
        content TEXT
        )
        """
        await self.execute(command=CommandType.ON_LOAD, query=query)

    async def insert_event(self, event: DBEvent) -> None:
        query = """
        INSERT INTO events(id, event_type, timestamp, guild_id, channel_id, member_id, message_id, content)
        VALUES(?,?,?,?,?,?,?,?)
        """
        data = (
            str(uuid.uuid4()),
            event.event_type,
            event.timestamp,
            event.guild_id,
            event.channel_id,
            event.member_id,
            event.message_id,
            event.content
        )
        await self.execute(command=CommandType.INSERT, query=query, parameters=data)

    async def get_events(self, start_time: int, stop_time: int):
        query = """
        SELECT event_type, timestamp, guild_id, channel_id, member_id, message_id, content
        FROM events
        WHERE timestamp
        BETWEEN (?) AND (?)
        """
        await self.execute(command=CommandType.GET, query=query, parameters=(start_time, stop_time))


async def event_db_builder(event: DiscordEvent) -> DBEvent:
    message_id = event.message.id if (event.type == EventTypeEnum.MESSAGE
                                      or event.type == EventTypeEnum.REACTION) else None
    return DBEvent(
        event_type=event.type,
        timestamp=event.timestamp.timestamp().__round__(),
        guild_id=event.guild.id,
        channel_id=event.channel.id,
        member_id=event.user.id,
        message_id=message_id,
        content=event.content
    )

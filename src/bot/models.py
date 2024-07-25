import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import aiosqlite


@dataclass
class DBEvent:
    event_type: str
    timestamp: int
    guild_id: int
    channel_id: int
    member_id: int
    message_id: Optional[int]
    content: Optional[str]


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
        self.db_name = guild_name.join("_events.db")

    async def execute(self, command: CommandType, query: str = None, data: tuple = None):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.cursor()
            match command:
                case CommandType.ON_LOAD:
                    await cursor.execute(query)
                    await db.commit()
                    print(f"database loaded successfully.")
                case CommandType.INSERT:
                    await cursor.execute(query, data)
                    await db.commit()
                    print(f"database insert successfully.")
                case CommandType.GET:
                    result = await db.execute(query)
                    return await result.fechall()

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
        INSERT INTO events(id, event_type, timestamp, guild_id, channel_id, member_id, message_id, message_cache)
        VALUES(?,?,?,?,?,?,?,?)
        """
        data = (str(uuid.uuid4()), event.event_type, event.timestamp, event.guild_id, event.channel_id, event.member_id,
                event.message_id, event.content)
        await self.execute(command=CommandType.INSERT, query=query, data=data)

    async def get_events(self, start_time: int, stop_time: int):
        query = """
        SELECT event_type, timestamp, guild_id, channel_id, member_id, message_id, content FROM events WHERE timestamp BETWEEN {} AND {}
        """.format(start_time, stop_time)
        await self.execute(command=CommandType.GET, query=query)

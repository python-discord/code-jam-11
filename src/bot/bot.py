import asyncio
import io
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime

import discord
from discord import app_commands

from ecosystem import EcosystemManager

from .settings import BOT_TOKEN, GIF_CHANNEL_ID, GUILD_ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s")

MAX_MESSAGES = 2


@dataclass
class DiscordEvent:
    type: str
    timestamp: datetime
    guild: discord.Guild
    channel: discord.TextChannel
    user: discord.User
    content: str


class EcoCordClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.test_guild = discord.Object(id=GUILD_ID)
        self.ecosystem_manager = None
        self.ready = False

    async def on_ready(self) -> None:
        self.ready = True
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    async def on_message(self, message: discord.Message) -> None:
        event = DiscordEvent(
            type="message",
            timestamp=message.created_at,
            guild=message.guild,
            channel=message.channel,
            user=message.author,
            content=message.content,
        )
        await self.process_event(event)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        event = DiscordEvent(
            type="reaction",
            timestamp=message.created_at,
            guild=self.get_guild(payload.guild_id),
            channel=channel,
            user=payload.member,
            content=f"{payload.emoji} added on {message.content}",
        )
        await self.process_event(event)

    async def on_raw_typing(self, payload: discord.RawTypingEvent) -> None:
        channel = self.get_channel(payload.channel_id)
        event = DiscordEvent(
            type="typing",
            timestamp=payload.timestamp,
            guild=self.get_guild(payload.guild_id),
            channel=channel,
            user=payload.user,
            content="User is typing",
        )
        await self.process_event(event)

    async def process_event(self, event: DiscordEvent) -> None:
        print(
            f"Event: {event.type} - {event.user.display_name} in {event.channel}: {event.content} @ {event.timestamp}"
        )
        if self.ecosystem_manager:
            self.ecosystem_manager.process_event(event)

    async def start_ecosystem(self) -> None:
        self.ecosystem_manager = EcosystemManager(generate_gifs=True)
        self.ecosystem_manager.start(show_controls=False)

    async def stop_ecosystem(self) -> None:
        if self.ecosystem_manager:
            self.ecosystem_manager.stop()

    async def find_existing_messages(self, channel: discord.TextChannel) -> list[discord.Message]:
        existing_messages = [
            message
            async for message in channel.history(limit=100)
            if message.author == self.user and message.content.startswith("Ecosystem")
        ]
        return sorted(existing_messages, key=lambda m: m.created_at)

    async def send_gifs(self) -> None:
        if not self.ecosystem_manager:
            return

        while not self.ready:
            await asyncio.sleep(1)

        channel = await self.fetch_channel(GIF_CHANNEL_ID)
        message_queue = deque(maxlen=MAX_MESSAGES)

        # Find existing messages and populate the queue
        existing_messages = await self.find_existing_messages(channel)
        # Delete all existing messages except the last max messages
        oldest_messages = existing_messages[:-MAX_MESSAGES]
        for message in oldest_messages:
            await message.delete()
        existing_messages = existing_messages[-MAX_MESSAGES:]
        message_queue.extend(existing_messages)

        while True:
            gif_data = self.ecosystem_manager.get_latest_gif()
            if not gif_data:
                await asyncio.sleep(0.01)
                continue

            gif_bytes, timestamp = gif_data

            content = "Ecosystem"

            # Send new message
            new_message = await channel.send(
                content=content, file=discord.File(io.BytesIO(gif_bytes), filename="ecosystem.gif")
            )

            # If the queue is full, the oldest message will be automatically removed
            # We need to delete it from Discord as well
            if len(message_queue) == MAX_MESSAGES:
                old_message = message_queue[0]
                await old_message.delete()

            message_queue.append(new_message)

    async def run_bot(self) -> None:
        print("Starting bot...")
        await self.start(BOT_TOKEN)

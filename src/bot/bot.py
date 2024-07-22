import asyncio
import io
import logging
from collections import deque

import discord
from discord import app_commands

from ecosystem import EcosystemManager

from .settings import BOT_TOKEN, GIF_CHANNEL_ID, GUILD_ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s")

MAX_MESSAGES = 2


class EcoCordClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.test_guild = discord.Object(id=GUILD_ID)
        self.ecosystem_manager = None
        self.ready = False

    async def on_ready(self):
        self.ready = True
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    async def on_message(self, message: discord.Message):
        print(f"{message.author.display_name} sent a message: {message.content} @ {message.created_at}")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        message_id = payload.message_id
        channel_id = payload.channel_id
        guild = self.get_guild(payload.guild_id)
        channel = guild.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        print(f"{payload.emoji} added on {message.content} @ {message.created_at}")

    async def on_raw_typing(self, payload: discord.RawTypingEvent):
        channel_id = payload.channel_id
        timestamp = payload.timestamp
        user = payload.user
        print("{user} is typing a message on channel {channel} @ {timestamp}")

    async def start_ecosystem(self):
        self.ecosystem_manager = EcosystemManager(generate_gifs=True)
        self.ecosystem_manager.start(show_controls=False)

    async def stop_ecosystem(self):
        if self.ecosystem_manager:
            self.ecosystem_manager.stop()

    async def find_existing_messages(self, channel):
        existing_messages = [
            message
            async for message in channel.history(limit=100)
            if message.author == self.user and message.content.startswith("Ecosystem")
        ]
        return sorted(existing_messages, key=lambda m: m.created_at)

    async def send_gifs(self):
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

    async def run_bot(self):
        print("Starting bot...")
        await self.start(BOT_TOKEN)

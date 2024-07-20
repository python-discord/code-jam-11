import asyncio

import discord
from discord import app_commands

from ecosystem import EcosystemManager

from .settings import BOT_TOKEN, GIF_CHANNEL_ID, GUILD_ID


class EcoCordClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.test_guild = discord.Object(id=GUILD_ID)
        self.ecosystem_manager = None
        self.ready = False

    async def setup_hook(self):
        self.tree.copy_global_to(guild=self.test_guild)
        await self.tree.sync(guild=self.test_guild)

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

    async def run_bot(self):
        print("Starting bot...")
        await self.start(BOT_TOKEN)

    async def start_ecosystem(self):
        self.ecosystem_manager = EcosystemManager(generate_gifs=True)
        self.ecosystem_manager.start(show_controls=False)

    async def stop_ecosystem(self):
        if self.ecosystem_manager:
            self.ecosystem_manager.stop()

    async def find_existing_message(self, channel):
        async for message in channel.history(limit=100):
            if message.author == self.user and message.content.startswith("Test"):
                return message
        return None

    async def send_gifs(self):
        if not self.ecosystem_manager:
            return

        while not self.ready:
            await asyncio.sleep(1)

        channel = await self.fetch_channel(GIF_CHANNEL_ID)

        message = await self.find_existing_message(channel)

        while True:
            gif_data = self.ecosystem_manager.get_latest_gif()
            if gif_data:
                gif_path, timestamp = gif_data

                if message is None:
                    message = await channel.send(content="Test", file=discord.File(gif_path))
                else:
                    await message.edit(content="Test", attachments=[discord.File(gif_path)])

            await asyncio.sleep(1)

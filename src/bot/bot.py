import asyncio
import io
import logging
from collections import deque

import discord
from discord import app_commands

from ecosystem import EcosystemManager

from .discord_event import DiscordEvent, EventType
from .models import EventsDatabase, event_db_builder
from .settings import BOT_TOKEN, GIF_CHANNEL_ID, GUILD_ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s")

MAX_MESSAGES = 2


class EcoCordClient(discord.Client):
    """A custom Discord client for managing multiple ecosystem simulations and handling Discord events."""

    def __init__(self) -> None:
        """Initialize the EcoCordClient with default intents and set up necessary attributes."""
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.test_guild = discord.Object(id=GUILD_ID)
        self.ecosystem_managers = {}
        self.ready = False
        self.guild = None
        self.events_database = None

    async def on_ready(self) -> None:
        """Event receiver for when the client is done preparing the data received from Discord.

        Sets the client as ready and prints a login confirmation message.
        """
        self.ready = True
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        await self.start_ecosystems()
        for guild in self.guilds:
            online_members = [member.id for member in guild.members if member.status != discord.Status.offline]
            self.ecosystem_manager.on_load_critters(online_members)
        self.events_database = EventsDatabase(self.guild.name)
        await self.events_database.load_table()

    async def on_message(self, message: discord.Message) -> None:
        """Event receiver for when a message is sent in a visible channel.

        Creates a DiscordEvent for the message and processes it.

        Args:
        ----
            message (discord.Message): The message that was sent.

        """
        event = DiscordEvent.from_discord_objects(
            type=EventType.MESSAGE,
            timestamp=message.created_at,
            guild=message.guild,
            channel=message.channel,
            member=message.author,
            content=message.content,
        )
        await self.process_event(event)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """Event receiver for when a message reaction is added to a message.

        Creates a DiscordEvent for the reaction and processes it.

        Args:
        ----
            payload (discord.RawReactionActionEvent): The raw event payload for the reaction.

        """
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        event = DiscordEvent.from_discord_objects(
            type=EventType.REACTION,
            timestamp=message.created_at,
            guild=self.get_guild(payload.guild_id),
            channel=channel,
            member=payload.member,
            content=f"{payload.emoji} added on {message.content}",
        )
        await self.process_event(event)

    async def on_raw_typing(self, payload: discord.RawTypingEvent) -> None:
        """Event receiver for when a user starts typing in a channel.

        Creates a DiscordEvent for the typing action and processes it.

        Args:
        ----
            payload (discord.RawTypingEvent): The raw event payload for the typing action.

        """
        channel = self.get_channel(payload.channel_id)
        event = DiscordEvent.from_discord_objects(
            type=EventType.TYPING,
            timestamp=payload.timestamp,
            guild=self.get_guild(payload.guild_id),
            channel=channel,
            member=payload.user,
            content="User is typing",
        )
        await self.process_event(event)

    async def process_event(self, event: DiscordEvent) -> None:
        """Process a DiscordEvent by logging it and passing it to the corresponding ecosystem manager."""
        print(
            f"Event: {event.type.name} - {event.member.display_name} in {event.channel}: "
            f"{event.content} @ {event.timestamp}"
        )
        ecosystem_manager = self.ecosystem_managers.get(event.channel.id)
        if ecosystem_manager:
            ecosystem_manager.process_event(event)
        db_event = await event_db_builder(event)
        await self.events_database.insert_event(db_event)

    async def start_ecosystems(self) -> None:
        """Initialize and start ecosystem managers for each channel and create or reuse GIF threads."""
        gif_channel = await self.fetch_channel(GIF_CHANNEL_ID)

        existing_threads = {thread.name: thread for thread in gif_channel.threads}

        gif_tasks = []
        for channel in self.get_all_channels():
            if isinstance(channel, discord.TextChannel):
                ecosystem_manager = EcosystemManager(generate_gifs=True, interactive=False)
                ecosystem_manager.start(show_controls=False)
                self.ecosystem_managers[channel.id] = ecosystem_manager

                thread_name = f"Ecosystem-{channel.name}"
                if thread_name in existing_threads:
                    thread = existing_threads[thread_name]
                    print(f"Reusing existing thread for {channel.name}")
                else:
                    thread = await gif_channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
                    print(f"Created new thread for {channel.name}")

                gif_tasks.append(self.send_gifs(channel.id, thread.id))

        # Start all gif sending tasks in parallel
        await asyncio.gather(*gif_tasks)

    async def stop_ecosystems(self) -> None:
        """Stop all ecosystem managers."""
        for ecosystem_manager in self.ecosystem_managers.values():
            ecosystem_manager.stop()

        self.ecosystem_managers.clear()

    async def send_gifs(self, channel_id: int, thread_id: int) -> None:
        """Continuously sends GIFs of the ecosystem to a designated thread."""
        ecosystem_manager = self.ecosystem_managers.get(channel_id)
        if not ecosystem_manager:
            return

        while not self.ready:
            await asyncio.sleep(1)

        thread = await self.fetch_channel(thread_id)
        message_queue = deque(maxlen=MAX_MESSAGES)

        # Find existing messages and populate the queue
        existing_messages = await self.find_existing_messages(thread)
        # Delete all existing messages except the last max messages
        oldest_messages = existing_messages[:-MAX_MESSAGES]
        for message in oldest_messages:
            await message.delete()
        existing_messages = existing_messages[-MAX_MESSAGES:]
        message_queue.extend(existing_messages)

        while True:
            gif_data = ecosystem_manager.get_latest_gif()
            if not gif_data:
                await asyncio.sleep(0.01)
                continue

            gif_bytes, timestamp = gif_data

            content = f"Ecosystem for #{self.get_channel(channel_id).name}"
            # Send new message
            new_message = await thread.send(
                content=content, file=discord.File(io.BytesIO(gif_bytes), filename="ecosystem.gif")
            )

            # If the queue is full, the oldest message will be automatically removed
            # We need to delete it from Discord as well
            if len(message_queue) == MAX_MESSAGES:
                old_message = message_queue[0]
                await old_message.delete()

            message_queue.append(new_message)

    async def find_existing_messages(self, channel: discord.TextChannel) -> list[discord.Message]:
        """Find existing ecosystem messages in the given channel.

        Args:
        ----
            channel (discord.TextChannel): The channel to search for messages.

        Returns:
        -------
            list[discord.Message]: A list of existing ecosystem messages, sorted by creation time.

        """
        existing_messages = [
            message
            async for message in channel.history(limit=100)
            if message.author == self.user and message.content.startswith("Ecosystem")
        ]
        return sorted(existing_messages, key=lambda m: m.created_at)

    async def run_bot(self) -> None:
        """Start the bot and connects to Discord."""
        print("Starting bot...")
        await self.start(BOT_TOKEN)

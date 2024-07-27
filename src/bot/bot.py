import asyncio
import io
import logging
from collections import deque

import discord
from discord import app_commands, ui

from ecosystem import EcosystemManager

from .discord_event import DiscordEvent, EventType
from .models import EventsDatabase, event_db_builder
from .settings import BOT_TOKEN

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s")

MAX_MESSAGES = 2


class EcoCordClient(discord.Client):
    """A custom Discord client for managing multiple ecosystem simulations and handling Discord events."""

    def __init__(self) -> None:
        """Initialize the EcoCordClient with default intents and set up necessary attributes."""
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.guilds_data = {}
        self.ready = False

    async def on_ready(self) -> None:
        """Event receiver for when the client is done preparing the data received from Discord.

        Sets the client as ready and prints a login confirmation message.
        """
        self.ready = True
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        for guild in self.guilds:
            await self.initialize_guild(guild)

    async def initialize_guild(self, guild: discord.Guild) -> None:
        if guild.id not in self.guilds_data:
            self.guilds_data[guild.id] = {
                "ecosystem_managers": {},
                "events_database": EventsDatabase(guild.name),
                "gif_channel_id": None,  # Initialize with None
            }
            await self.guilds_data[guild.id]["events_database"].load_table()

        online_members = [member.id for member in guild.members if member.status != discord.Status.offline]
        for ecosystem_manager in self.guilds_data[guild.id]["ecosystem_managers"].values():
            ecosystem_manager.on_load_critters(online_members)

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
        guild_data = self.guilds_data.get(event.guild.id)
        if guild_data:
            ecosystem_manager = guild_data["ecosystem_managers"].get(event.channel.id)
            if ecosystem_manager:
                ecosystem_manager.process_event(event)
            db_event = await event_db_builder(event)
            await guild_data["events_database"].insert_event(db_event)

    async def start_ecosystems(self, guild_id: int, channels: list[discord.TextChannel] | None = None) -> None:
        """Initialize and start ecosystem managers for specified channels."""
        guild_data = self.guilds_data.get(guild_id)
        if not guild_data or guild_data["gif_channel_id"] is None:
            return

        gif_channel = await self.fetch_channel(guild_data["gif_channel_id"])
        existing_threads = {thread.name: thread for thread in gif_channel.threads}

        gif_tasks = []

        for channel in channels:
            if channel.id not in guild_data["ecosystem_managers"]:
                ecosystem_manager = EcosystemManager(generate_gifs=True, interactive=False)
                ecosystem_manager.start(show_controls=False)
                guild_data["ecosystem_managers"][channel.id] = ecosystem_manager

                thread_name = f"Ecosystem-{channel.name}"
                if thread_name in existing_threads:
                    thread = existing_threads[thread_name]
                    print(f"Reusing existing thread for {channel.name}")
                else:
                    thread = await gif_channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
                    print(f"Created new thread for {channel.name}")

                gif_tasks.append(self.send_gifs(guild_id, channel.id, thread.id))

        # Start all new gif sending tasks in parallel
        await asyncio.gather(*gif_tasks)

    async def stop_ecosystems(self, guild_id: int, channel_ids: list[int] | None = None) -> None:
        """Stop specified ecosystem managers or all if not specified."""
        guild_data = self.guilds_data.get(guild_id)
        if not guild_data:
            return

        if channel_ids is None:
            channel_ids = list(guild_data["ecosystem_managers"].keys())

        for channel_id in channel_ids:
            ecosystem_manager = guild_data["ecosystem_managers"].pop(channel_id, None)
            if ecosystem_manager:
                ecosystem_manager.stop()

    async def reconfigure_channels(self, guild_id: int, new_channels: list[discord.TextChannel]) -> None:
        """Reconfigure the bot to run in the specified channels."""
        guild_data = self.guilds_data.get(guild_id)
        if not guild_data:
            return

        new_channel_ids = {channel.id for channel in new_channels}
        current_channel_ids = set(guild_data["ecosystem_managers"].keys())

        channels_to_stop = current_channel_ids - new_channel_ids
        channels_to_start = new_channel_ids - current_channel_ids

        await self.stop_ecosystems(guild_id, list(channels_to_stop))
        await self.start_ecosystems(guild_id, [channel for channel in new_channels if channel.id in channels_to_start])

    async def send_gifs(self, guild_id: int, channel_id: int, thread_id: int) -> None:
        """Continuously sends GIFs of the ecosystem to a designated thread."""
        guild_data = self.guilds_data.get(guild_id)
        if not guild_data:
            return

        ecosystem_manager = guild_data["ecosystem_managers"].get(channel_id)
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

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Event receiver for when the bot joins a new guild."""
        await self.initialize_guild(guild)

        # Find a channel visible to admins (e.g., a "general" or "admin" channel)
        admin_channel = next(
            (
                channel
                for channel in guild.text_channels
                if channel.permissions_for(guild.me).send_messages
                and channel.overwrites_for(guild.default_role).read_messages is not False
                and any(
                    role.permissions.administrator
                    for role in guild.roles
                    if channel.overwrites_for(role).read_messages is not False
                )
            ),
            None,
        )

        if admin_channel:
            embed = discord.Embed(
                title="EcoCord Bot Installed!",
                description="Bot installed. Admins can use `/configure` to set it up.",
                color=discord.Color.blue(),
            )

            try:
                await admin_channel.send(embed=embed)
                logging.info(
                    "Sent welcome message in guild %s (ID: %s) in channel %s", guild.name, guild.id, admin_channel.name
                )
            except discord.errors.Forbidden:
                logging.warning(
                    "Failed to send welcome message in guild %s (ID: %s) due to permissions", guild.name, guild.id
                )
        else:
            logging.warning(
                "Couldn't find suitable channel to send welcome message in guild %s (ID: %s)", guild.name, guild.id
            )

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Event receiver for when the bot is removed from a guild."""
        if guild.id in self.guilds_data:
            # Stop all ecosystem managers for this guild
            await self.stop_ecosystems(guild.id)
            # Remove the guild data
            del self.guilds_data[guild.id]
        logging.info("Removed from guild %s (ID: %s)", guild.name, guild.id)

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def configure(self, interaction: discord.Interaction) -> None:
        """Configure the bot (Admin only)."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        modal = ConfigureModal()
        await interaction.response.send_modal(modal)


class ConfigureModal(ui.Modal, title="Configure EcoCord Bot"):
    """Modal for configuring the EcoCord Bot."""

    channel_select = ui.ChannelSelect(
        placeholder="Select channels for ecosystem simulation",
        min_values=1,
        max_values=10,
        channel_types=[discord.ChannelType.text],
    )
    gif_channel = ui.ChannelSelect(
        placeholder="Select channel for GIF threads",
        min_values=1,
        max_values=1,
        channel_types=[discord.ChannelType.text],
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        channels = [channel.name for channel in self.channel_select.to_numpy()]
        gif_channel = self.gif_channel.to_numpy()[0]

        client = interaction.client
        guild_data = client.guilds_data.get(interaction.guild_id)
        if guild_data:
            guild_data["gif_channel_id"] = gif_channel.id

        await interaction.response.send_message(
            f"Bot configured to run in channels: {', '.join(channels)}\n"
            f"GIF threads will be created in: #{gif_channel.name}",
            ephemeral=True,
        )

        await client.reconfigure_channels(interaction.guild_id, self.channel_select.to_numpy())

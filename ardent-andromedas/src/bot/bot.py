import asyncio
import io
import logging
from collections import deque
from collections.abc import Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
import discord
from discord import app_commands

from ecosystem import EcosystemManager
from storage.models import Database, GuildConfig, UserInfo

from .discord_event import DiscordEvent, EventType, SerializableMember
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
        self.tree.add_command(configure)
        self.guilds_data = {}
        self.ready = False
        self.database = Database("ecocord")

    async def on_ready(self) -> None:
        """Event receiver for when the client is done preparing the data received from Discord."""
        await self.database.initialize()
        self.ready = True
        print(f"Logged in as {self.user} (ID: {self.user.id})")

        for guild in self.guilds:
            await self.tree.sync(guild=guild)
            await self.initialize_guild(guild)

    async def initialize_guild(self, guild: discord.Guild) -> None:
        """Initialize the guild data and ecosystem managers for a given Discord guild.

        This method sets up the necessary data structures for the guild, retrieves the guild configuration
        from the database, and initializes ecosystem managers for the configured channels. It also loads
        critters for online members in each ecosystem manager.

        Args:
        ----
            guild (discord.Guild): The Discord guild to initialize.

        Returns:
        -------
            None

        """
        if guild.id not in self.guilds_data:
            self.guilds_data[guild.id] = {
                "ecosystem_managers": {},
            }
            config = await self.database.get_guild_config(guild.id)
            if config:
                self.guilds_data[guild.id]["gif_channel_id"] = config.gif_channel
                # Call reconfigure_channels here with the channels from the config
                channels = [guild.get_channel(channel_id) for channel_id in config.allowed_channels]
                await self.reconfigure_channels(guild.id, channels)

    async def on_message(self, message: discord.Message) -> None:
        """Event receiver for when a message is sent in a visible channel.

        Creates a DiscordEvent for the message and processes it.

        Args:
        ----
            message (discord.Message): The message that was sent.

        """
        # Check if the message is a direct message
        is_direct_message = isinstance(message.channel, discord.DMChannel)

        # If it's a direct message, we'll handle it differently
        if is_direct_message:
            return

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

        # Fetch the reaction image
        reaction_image_bytes = await self.get_reaction_image(payload.emoji)

        event = DiscordEvent.from_discord_objects(
            type=EventType.REACTION,
            timestamp=message.created_at,
            guild=self.get_guild(payload.guild_id),
            channel=channel,
            member=payload.member,
            content=f"{payload.emoji} added on {message.content}",
            reaction_image=reaction_image_bytes,
        )
        await self.process_event(event)

    async def get_reaction_image(self, emoji_obj: discord.PartialEmoji | str) -> bytes | None:
        """Fetch the image data for a given emoji."""
        if not isinstance(emoji_obj, discord.PartialEmoji):
            return None

        if emoji_obj.is_custom_emoji():
            emoji_url = str(emoji_obj.url)
            async with aiohttp.ClientSession() as session, session.get(emoji_url) as response:
                if response.status == 200:
                    return await response.read()

        return None

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

    async def get_user_info(self, member: discord.Member | SerializableMember) -> UserInfo:
        """Fetch and store user avatar and role color for a specific guild."""
        now = datetime.now(UTC)

        # Check if member is a SerializableMember or discord.Member
        if isinstance(member, SerializableMember):
            user_id = member.id
            guild_id = member.guild_id
        else:  # discord.Member
            user_id = member.id
            guild_id = member.guild.id

        user_info = await self.database.get_user_info(user_id, guild_id)

        if user_info is None or (now - user_info.last_updated) > timedelta(hours=1):
            if isinstance(member, SerializableMember):
                avatar_url = member.avatar
                role_color = member.color
            else:  # discord.Member
                avatar_url = str(member.avatar.url) if member.avatar else None
                role_color = str(member.color)

            if avatar_url:
                async with aiohttp.ClientSession() as session, session.get(avatar_url) as resp:
                    avatar_data = await resp.read()
            else:
                avatar_data = None

            user_info = UserInfo(
                user_id=user_id, guild_id=guild_id, avatar_data=avatar_data, role_color=role_color, last_updated=now
            )
            await self.database.set_user_info(user_info)

        return user_info

    async def process_event(self, event: DiscordEvent) -> None:
        """Process a DiscordEvent by logging it and passing it to the corresponding ecosystem manager."""
        if event.member.id == self.user.id:
            return

        print(
            f"Event: {event.type.name} - {event.member.display_name} in {event.channel}: "
            f"{event.content} @ {event.timestamp}"
        )
        guild_data = self.guilds_data.get(event.guild.id)
        if guild_data:
            ecosystem_manager = guild_data["ecosystem_managers"].get(event.channel.id)
            if ecosystem_manager:
                user_info = await self.get_user_info(event.member)
                ecosystem_manager.process_event(event, user_info)

    async def start_ecosystems(self, guild_id: int, channels: list[discord.TextChannel] | None = None) -> None:
        """Initialize and start ecosystem managers for specified channels."""
        guild_data = self.guilds_data.get(guild_id)
        if not guild_data or guild_data["gif_channel_id"] is None:
            return

        gif_channel = await self.fetch_channel(guild_data["gif_channel_id"])
        existing_threads = {thread.name: thread for thread in gif_channel.threads}

        for channel in channels:
            if channel.id in guild_data["ecosystem_managers"]:
                continue
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

            # Start the gif sending task in the background
            self.loop.create_task(
                self.safe_task(
                    self.send_gifs(guild_id, channel.id, thread.id),
                    f"send_gifs for channel {channel.name} in guild {guild_id}",
                )
            )

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

    async def stop_all_ecosystems(self) -> None:
        """Stop all ecosystem managers for all guilds."""
        for guild_data in self.guilds_data.values():
            ecosystem_managers = guild_data.get("ecosystem_managers", {})
            for ecosystem_manager in ecosystem_managers.values():
                ecosystem_manager.stop()
            guild_data["ecosystem_managers"] = {}

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

        # Update the guild configuration in the database
        config = GuildConfig(
            guild_id=guild_id, allowed_channels=list(new_channel_ids), gif_channel=guild_data["gif_channel_id"]
        )
        await self.database.set_guild_config(config)

    async def send_gifs(self, guild_id: int, channel_id: int, thread_id: int) -> None:
        """Continuously sends GIFs of the ecosystem to a designated thread."""
        while not self.ready:
            await asyncio.sleep(1)

        try:
            thread = await self.fetch_channel(thread_id)
        except discord.errors.NotFound:
            logging.exception("Thread %s not found. Stopping GIF sending for channel %s", thread_id, channel_id)
            return

        message_queue = deque(maxlen=MAX_MESSAGES)

        # Find existing messages and populate the queue
        try:
            existing_messages = await self.find_existing_messages(thread)
            # Delete all existing messages except the last max messages
            oldest_messages = existing_messages[:-MAX_MESSAGES]
            for message in oldest_messages:
                await message.delete()
            existing_messages = existing_messages[-MAX_MESSAGES:]
            message_queue.extend(existing_messages)
        except Exception:
            logging.exception("Error processing existing messages")

        while True:
            try:
                guild_data = self.guilds_data.get(guild_id)
                if not guild_data:
                    logging.warning("Guild data not found for guild %s. Stopping GIF sending.", guild_id)
                    return

                ecosystem_manager = guild_data["ecosystem_managers"].get(channel_id)
                if not ecosystem_manager:
                    logging.warning("Ecosystem manager not found for channel %s. Stopping GIF sending.", channel_id)
                    return

                gif_data = ecosystem_manager.get_latest_gif()
                if not gif_data:
                    await asyncio.sleep(0.01)
                    continue

                gif_bytes, timestamp = gif_data

                logging.info("Sending new ecosystem GIF message to thread %s in guild %s", thread_id, guild_id)

                retry_count = 0
                while retry_count < 3:
                    try:
                        new_message = await thread.send(
                            file=discord.File(io.BytesIO(gif_bytes), filename="ecosystem.gif")
                        )
                        break
                    except discord.errors.HTTPException as e:
                        retry_count += 1
                        logging.warning("Failed to send GIF (attempt %d): %s", retry_count, str(e))
                        await asyncio.sleep(5)
                else:
                    logging.error("Failed to send GIF after 3 attempts. Skipping this update.")
                    continue

                # If the queue is full, the oldest message will be automatically removed
                # We need to delete it from Discord as well
                if len(message_queue) == MAX_MESSAGES:
                    old_message = message_queue[0]
                    try:
                        await old_message.delete()
                    except discord.errors.NotFound:
                        logging.warning("Old message not found, it may have been deleted already.")

                message_queue.append(new_message)

            except Exception:
                logging.exception("Unexpected error in send_gifs")
                await asyncio.sleep(10)  # Wait a bit before retrying the whole loop

    async def find_existing_messages(self, channel: discord.TextChannel) -> list[discord.Message]:
        """Find existing ecosystem messages in the given channel.

        Args:
        ----
            channel (discord.TextChannel): The channel to search for messages.

        Returns:
        -------
            list[discord.Message]: A list of existing ecosystem messages, sorted by creation time.

        """
        existing_messages = [message async for message in channel.history(limit=100) if message.author == self.user]
        return sorted(existing_messages, key=lambda m: m.created_at)

    async def run_bot(self) -> None:
        """Start the bot and connects to Discord."""
        print("Starting bot...")
        if not BOT_TOKEN:
            error_message = "BOT_TOKEN is not set"
            raise ValueError(error_message)
        await self.start(BOT_TOKEN)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Event receiver for when the bot joins a new guild."""
        await self.initialize_guild(guild)

        embed = discord.Embed(
            title="EcoCord Bot Installed!",
            description="Bot installed. Admins can use `/configure` to set it up.",
            color=discord.Color.blue(),
        )

        # Separate channels into admin-visible and others
        admin_channels = []
        other_channels = []

        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                if channel.overwrites_for(guild.default_role).read_messages is not False and any(
                    role.permissions.administrator
                    for role in guild.roles
                    if channel.overwrites_for(role).read_messages is not False
                ):
                    admin_channels.append(channel)
                else:
                    other_channels.append(channel)

        # Try admin channels first, then other channels
        for channel in admin_channels + other_channels:
            try:
                await channel.send(embed=embed)
                logging.info(
                    "Sent welcome message in guild %s (ID: %s) in channel %s", guild.name, guild.id, channel.name
                )
            except discord.errors.Forbidden:
                continue  # Try the next channel if this one didn't work
            else:
                return  # Exit the method after successfully sending the message
        # If we've gone through all channels and couldn't send the message
        logging.warning(
            "Couldn't find any suitable channel to send welcome message in guild %s (ID: %s)", guild.name, guild.id
        )

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Event receiver for when the bot is removed from a guild."""
        if guild.id in self.guilds_data:
            # Stop all ecosystem managers for this guild
            await self.stop_ecosystems(guild.id)
            # Remove the guild data
            del self.guilds_data[guild.id]
        logging.info("Removed from guild %s (ID: %s)", guild.name, guild.id)

    async def safe_task(self, coro: Coroutine[Any, Any, Any], task_name: str) -> None:
        try:
            await coro
        except Exception as e:  # noqa: BLE001
            print(f"Exception in {task_name}: {e!s}")
            import traceback

            traceback.print_exc()


class ConfigureView(discord.ui.View):
    """View for configuring EcoCord."""

    def __init__(self, client: discord.Client, guild_id: int, visible_channels: list[discord.TextChannel]) -> None:
        """Initialize the ConfigureView.

        Args:
        ----
            client: The Discord client.
            guild_id: The ID of the guild being configured.
            visible_channels: List of visible text channels in the guild.

        """
        super().__init__()
        self.client = client
        self.guild_id = guild_id
        self.visible_channels = visible_channels

        # Get existing configuration
        guild_data = self.client.guilds_data.get(self.guild_id, {})
        self.managed_channels = [
            channel for channel in visible_channels if channel.id in guild_data.get("ecosystem_managers", {})
        ]
        self.gif_channel = next(
            (channel for channel in visible_channels if channel.id == guild_data.get("gif_channel_id")), None
        )

        # Add managed channels select
        self.add_item(
            discord.ui.ChannelSelect(
                custom_id="managed_channels",
                placeholder="Select managed channels",
                min_values=1,
                max_values=len(visible_channels),
                channel_types=[discord.ChannelType.text],
                default_values=self.managed_channels,
            )
        )

        # Add GIF channel select
        self.add_item(
            discord.ui.ChannelSelect(
                custom_id="gif_channel",
                placeholder="Select GIF channel",
                min_values=1,
                max_values=1,
                channel_types=[discord.ChannelType.text],
                default_values=[self.gif_channel] if self.gif_channel else None,
            )
        )

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary)
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.on_submit(interaction)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        client = interaction.client
        guild_data = client.guilds_data.get(interaction.guild.id)

        if not self.managed_channels or not self.gif_channel:
            await interaction.response.send_message(
                "Please select both managed channels and a GIF channel before submitting.", ephemeral=True
            )
            return

        if guild_data:
            guild_data["gif_channel_id"] = self.gif_channel.id

        # Update the guild configuration in the database
        config = GuildConfig(
            guild_id=interaction.guild.id,
            allowed_channels=[channel.id for channel in self.managed_channels],
            gif_channel=self.gif_channel.id,
        )
        try:
            await client.database.set_guild_config(config)
        except Exception:
            logging.exception("Failed to update database")
            await interaction.followup.send(
                "An error occurred while saving the configuration. Please try again.", ephemeral=True
            )
            return

        confirmation_message = (
            "Configuration complete!\n\n"
            f"Bot configured to run in channels: {', '.join(channel.name for channel in self.managed_channels)}\n"
            f"GIF threads will be created in: #{self.gif_channel.name}"
        )

        try:
            message = await interaction.original_response()
            await message.edit(content=confirmation_message, view=None)
        except discord.NotFound:
            # If the original message was deleted, send a new message
            await interaction.followup.send(content=confirmation_message, ephemeral=True)

        try:
            await client.reconfigure_channels(interaction.guild.id, self.managed_channels)
        except Exception:
            logging.exception("Failed to reconfigure channels")
            await interaction.followup.send(
                "Configuration saved, but there was an error applying the changes. "
                "Please try again or contact support.",
                ephemeral=True,
            )

        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["component_type"] == discord.ComponentType.channel_select.value:
            if interaction.data["custom_id"] == "managed_channels":
                self.managed_channels = [
                    interaction.guild.get_channel(int(channel_id)) for channel_id in interaction.data["values"]
                ]
            elif interaction.data["custom_id"] == "gif_channel":
                self.gif_channel = interaction.guild.get_channel(int(interaction.data["values"][0]))

        # Acknowledge the interaction
        await interaction.response.defer()
        return True


@app_commands.command(name="configure", description="Configure EcoCord")
@app_commands.default_permissions(administrator=True)
async def configure(interaction: discord.Interaction) -> None:
    """Configure EcoCord settings for the guild."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    visible_channels = [
        channel
        for channel in interaction.guild.text_channels
        if channel.permissions_for(interaction.guild.me).send_messages
    ]
    view = ConfigureView(interaction.client, interaction.guild.id, visible_channels)
    await interaction.response.send_message("Please configure the bot:", view=view, ephemeral=True)

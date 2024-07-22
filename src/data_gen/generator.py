import asyncio
import random
from datetime import datetime

import discord
from discord.ext import tasks

from bot.settings import BOT_TOKEN_ARRAY as TOKENS

random_messages: list[str] = [
    "Hello everyone!",
    "How are u doing?",
    "Testing some bots!",
    "Anythin new!?",
    "Good morning or evening!",
    "Who is hungry?",
    "teeeeexxttt",
]


class EventGenerator(discord.Client):
    """A Discord bot client that generates random events and messages."""

    def __init__(self, token: str, intents: discord.Intents) -> None:
        """Initialize the EventGenerator.

        Args:
        ----
            token (str): The Discord bot token.
            intents (discord.Intents): The Discord intents for the bot.

        """
        super().__init__(intents=intents)
        self.token: str = token

    async def on_ready(self) -> None:
        """Event receiver for when the bot has successfully connected to Discord.

        Start the random message sending task.
        """
        print(f"{self.user} has connected to Discord!")
        self.send_random_message.start()

    @tasks.loop(seconds=5)
    async def send_random_message(self) -> None:
        """Send a random message to a random channel every 5 seconds."""
        print("Attempting to send a random message...")
        channels = list(self.get_all_channels())
        if not channels:
            print("No channels found.")
            return

        channel = random.choice(channels)
        print(f"Selected channel: {channel.name} (ID: {channel.id})")

        if isinstance(channel, discord.TextChannel):
            async with channel.typing():
                await asyncio.sleep(1)  # to simulate "Bot is typing..."
                message = random.choice(random_messages)
                print(f"Sending message: {message}")
                await channel.send(message)

    async def on_typing(self, channel: discord.abc.Messageable, user: discord.User, when: datetime.datetime) -> None:
        """Respond to typing events in channels.

        Sends a message if the typing user is a bot (excluding itself).

        Args:
        ----
            channel (discord.abc.Messageable): The channel where typing occurred.
            user (discord.User): The user who started typing.
            when (datetime.datetime): The time when typing started.

        """
        if user.bot and user != self.user:
            msg = f"@{user.name} is typing in #{channel.name} at `{when.hour:02}:{when.minute:02}:{when.second:02}`"
            await channel.send(msg)

    async def on_message(self, message: discord.Message) -> None:
        """React to messages sent in channels the bot can see.

        Adds a thumbs up reaction if the message content is "typing".

        Args:
        ----
            message (discord.Message): The message that was sent.

        """
        if message.author == self.user:
            return
        if message.content.lower() == "typing":
            await message.add_reaction("👍")

    async def start_bot(self) -> None:
        """Start the bot using the provided token."""
        print(f"Starting bot with token: {self.token[:5]}...")  # Log token (partially for security)
        try:
            await self.start(self.token)
        except discord.errors.LoginFailure as e:
            print(f"Login failed for token {self.token[:5]}: {e}")


async def run_bots() -> None:
    """Create and run multiple bot instances using the provided tokens."""
    intents = discord.Intents.all()
    bots = [EventGenerator(token, intents) for token in TOKENS]
    await asyncio.gather(*[bot.start_bot() for bot in bots])


if __name__ == "__main__":
    asyncio.run(run_bots())

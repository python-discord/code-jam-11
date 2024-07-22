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
    def __init__(self, token: str, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.token: str = token

    async def on_ready(self) -> None:
        print(f"{self.user} has connected to Discord!")
        self.send_random_message.start()

    @tasks.loop(seconds=5)
    async def send_random_message(self) -> None:
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
        if user.bot and user != self.user:
            msg = f"@{user.name} is typing in #{channel.name} at `{when.hour:02}:{when.minute:02}:{when.second:02}`"
            await channel.send(msg)

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return
        if message.content.lower() == "typing":
            await message.add_reaction("👍")

    async def start_bot(self) -> None:
        print(f"Starting bot with token: {self.token[:5]}...")  # Log token (partially for security)
        try:
            await self.start(self.token)
        except discord.errors.LoginFailure as e:
            print(f"Login failed for token {self.token[:5]}: {e}")


async def run_bots() -> None:
    intents = discord.Intents.all()
    bots = [EventGenerator(token, intents) for token in TOKENS]
    await asyncio.gather(*[bot.start_bot() for bot in bots])


if __name__ == "__main__":
    asyncio.run(run_bots())

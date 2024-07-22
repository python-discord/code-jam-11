import random
import asyncio
import discord

from discord.ext import tasks
#from src.bot.settings import BOT_TOKEN_ARRAY as TOKENS         "says the dir doesn't exist :("

TOKENS: list = [] # you can put the tokens here as a temporal solution, works the same way

random_messages: list = [
    "Hello everyone!",
    "How are u doing?",
    "Testing some bots!",
    "Anythin new!?",
    "Good morning or evening!",
    "Who is hungry?",
    "teeeeexxttt"
]



class EventGenerator(discord.Client):
    def __init__(self, token, intents, *args, **kwargs):
        super().__init__(intents=intents, *args, **kwargs)
        self.token = token


    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        self.send_random_message.start()


    @tasks.loop(seconds=5)
    async def send_random_message(self):
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


    async def on_typing(self, channel, user, when):
        if user.bot and user != self.user:
            msg = f"@{user.name} is typing in #{channel.name} at `{when.hour:02}:{when.minute:02}:{when.second:02}`"
            await channel.send(msg)


    async def on_message(self, message):
        if message.author == self.user:
            return
        elif message.content.lower() == "typing":
            await message.add_reaction("👍")


    async def start_bot(self):
        print(f"Starting bot with token: {self.token[:5]}...")  # Log token (partially for security)
        try:
            await self.start(self.token)
        except discord.errors.LoginFailure as e:
            print(f"Login failed for token {self.token[:5]}: {e}")



async def run_bots():
    intents = discord.Intents.all()
    bots = [EventGenerator(token, intents) for token in TOKENS]
    await asyncio.gather(*[bot.start_bot() for bot in bots])



if __name__ == "__main__":
    asyncio.run(run_bots())

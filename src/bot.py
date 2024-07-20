import discord
from discord import app_commands

from settings import BOT_TOKEN, GUILD_ID

TEST_GUILD = discord.Object(id=GUILD_ID)


class EcoCordClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=TEST_GUILD)
        await self.tree.sync(guild=TEST_GUILD)


client = EcoCordClient(intents=discord.Intents.default())


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


@client.event
async def on_message(message: discord.Message):
    print(f"{message.author.display_name} sent a message: {message.content} @ {message.created_at}")


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    message_id = payload.message_id
    channel_id = payload.channel_id
    guild = client.get_guild(payload.guild_id)
    channel = guild.get_channel(channel_id)
    message = await channel.fetch_message(message_id)
    print(f"{payload.emoji} added on {message.content} @ {message.created_at}")


client.run(BOT_TOKEN)

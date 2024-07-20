import discord
from discord import app_commands

from settings import BOT_TOKEN, GUILD_ID

MY_GUILD = discord.Object(id=GUILD_ID)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


client = MyClient(intents=discord.Intents.default())


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.context_menu(name='Show Member Messages')
async def show_member_data(interaction: discord.Interaction, member: discord.Member):
    # TO REMOVE
    messages = [message.content async for message in interaction.channel.history(limit=100, oldest_first=True) if message.author == member]
    await interaction.response.send_message(f'Message history of {member.display_name}: {messages}')


client.run(BOT_TOKEN)
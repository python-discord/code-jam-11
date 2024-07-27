import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Imports the commands
from cmds import (
    challenge,
    help_bot,
    leaderboard,
    never,
    rabbit_hole,
    reset_scores,
    sync,
    user_info,
    wikiguesser,
    wikirandom,
    wikisearch,
)

# loads the enviroment variables and initilazies the discord client
load_dotenv(".env")
intents = discord.Intents.all()
client = discord.Client(intents=intents)
client.tree = app_commands.CommandTree(client)

has_ran = False


async def _first_run(client: commands.Bot) -> None:
    """Sync command tree and update the app's discord status."""
    has_ran = True
    await client.tree.sync()
    logging.info("The sync has been ran: %s", has_ran)
    await client.change_presence(
        status=discord.Status.online,
        activity=discord.activity.CustomActivity("📚 reading wikipedia", emoji="📚"),
    )


@client.event
async def on_ready() -> None:
    """Start the client."""
    logging.info("ready for ACTION!!!")
    if not has_ran:
        await _first_run(client=client)


@client.event
async def on_guild_join(guild: discord.Object) -> None:
    """Declare the on guild join to sync it."""
    await client.tree.sync(guild=guild)
    logging.info("Joined and synced with \nname: %s\nid: %s", guild.name, guild.id)


# activates the commands
sync.main(client.tree)
wikiguesser.main(client.tree)
wikirandom.main(client.tree)
leaderboard.main(client.tree)
user_info.main(client.tree)
wikisearch.main(client.tree)
reset_scores.main(client.tree)
never.main(client.tree)
challenge.main(client.tree)
help_bot.main(client.tree)
rabbit_hole.main(client.tree)

# activates shutdown command if the app is running on the server
if bool(os.environ.get("SERVER", 0)):
    from cmds import shutdown

    shutdown.main(client.tree)

# runs the client
client.run(
    os.environ["DISAPI"],
    log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    root_logger=True,
)

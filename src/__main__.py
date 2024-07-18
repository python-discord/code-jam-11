# ruff: noqa: T201
import os

import discord

bot = discord.Bot()


BOT_TOKEN = os.environ["BOT_TOKEN"]


@bot.event
async def on_ready() -> None:
    """Function called once the bot is ready and online."""
    print(f"{bot.user} is ready and online!")


@bot.slash_command()
async def ping(ctx: discord.ApplicationContext) -> None:
    """Test out bot's latency."""
    _ = await ctx.respond(f"Pong! ({(bot.latency * 1000):.2f}ms)")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)

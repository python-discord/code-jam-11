import discord
from discord import app_commands

from wikiutils import make_embed, search_wikipedia


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    @tree.command(
        name="wiki-search",
        description="get a wikipedia article that you searched for",
    )
    async def wiki(interaction: discord.Interaction, query:str) -> None:
        await interaction.response.send_message(content="Finding your really cool article...")
        embed = make_embed(article=search_wikipedia(query))
        await interaction.followup.send(embed=embed)
        await interaction.delete_original_response()

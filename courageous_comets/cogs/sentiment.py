import logging
from pathlib import Path

import discord
import matplotlib.pyplot as plt
from discord import app_commands
from discord.ext import commands

from courageous_comets import models
from courageous_comets.client import CourageousCometsBot
from courageous_comets.enums import StatisticScope
from courageous_comets.redis.keys import key_schema
from courageous_comets.redis.messages import (
    get_average_sentiment,
    get_message_sentiment,
)
from courageous_comets.utils import contextmenu
from courageous_comets.vectorizer import Vectorizer

logger = logging.getLogger(__name__)


class MessagesNotFound(app_commands.AppCommandError):
    """No messages were found."""


SENTIMENT: dict[range, str] = {
    range(-100, -50): "very negative 😡",
    range(-50, -10): "negative 🙁",
    range(-10, 10): "neutral 🙂",
    range(10, 50): "positive 😁",
    range(50, 100): "very positive 😍",
}


MESSAGE_SENTIMENT_TEMPLATE = """
Overall the sentiment of the message is **{sentiment}**.

Here's a breakdown of the scores:

- Negative: {neg}
- Neutral: {neu}
- Positive: {pos}

The compound score is {compound}.
"""

USER_SENTIMENT_TEMPLATE = """
Overall the sentiment of {user} is **{sentiment}**.

Their average compound score is {compound}.
"""


def plot_sentiment_analysis(
    message_id: str | int,
    analysis_result: models.SentimentResult,
) -> Path:
    """
    Plot the sentiment analysis of a message.

    Creates a bar chart of the sentiment analysis of a message and saves it to a file.
    If the file already exists, it will be returned instead of being recreated.

    Parameters
    ----------
    message_id : str | int
        The id of the message.
    analysis_result : SentimentResult
        The result of sentiment analysis on a message.

    Returns
    -------
    Path
        The path to the saved image.
    """
    chart_dir = Path("artifacts/charts/sentiment").resolve()
    chart_dir.mkdir(parents=True, exist_ok=True)
    chart_path = chart_dir / f"{message_id}.png"

    if chart_path.exists():
        return chart_path

    _, ax = plt.subplots()
    ax.bar(
        [
            "Negative",
            "Neutral",
            "Positive",
        ],
        [
            analysis_result.neg,
            analysis_result.neu,
            analysis_result.pos,
        ],
        color=[
            "red",
            "blue",
            "green",
        ],
    )
    ax.set_ylabel("Sentiment Score")
    ax.set_title("Sentiment Analysis")

    plt.savefig(chart_path)

    return chart_path


class Sentiment(commands.Cog):
    """Sentiment related commands."""

    def __init__(self, bot: CourageousCometsBot) -> None:
        self.bot = bot

        self.vectorizer = Vectorizer()

        for attribute in dir(self):
            obj = getattr(self, attribute, None)
            if obj and getattr(obj, "is_contextmenu", False):
                menu = app_commands.ContextMenu(name=obj.name, callback=obj)
                self.bot.tree.add_command(menu)

    @contextmenu(name="Show user sentiment")
    async def show_user_sentiment(
        self,
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        """
        Allow users to view the sentiment analysis of a user using a context menu.

        Generates an embed with the sentiment analysis of a user and sends it to the user.

        The embed contains a line chart of the sentiment of a user over time.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        user : discord.User | discord.Member
            The user to analyze.
        """
        logger.info(
            "User %s requested sentiment analysis results for user %s.",
            interaction.user.id,
            user.id,
        )

        if self.bot.redis is None:
            return await interaction.response.send_message(
                "This feature is currently unavailable. Please try again later.",
                ephemeral=True,
            )

        if interaction.guild is None:
            return await interaction.response.send_message(
                "This feature is only available in guilds.",
                ephemeral=True,
            )

        user_sentiment = await get_average_sentiment(
            redis=self.bot.redis,
            guild_id=str(interaction.guild.id),
            ids=[str(user.id)],
            scope=StatisticScope.USER,
        )

        if not user_sentiment:
            raise MessagesNotFound

        average_sentiment = user_sentiment[0]["avg_sentiment"]

        sentiment = next(
            (value for key, value in SENTIMENT.items() if int(average_sentiment * 100) in key),
            "unknown",
        )

        if not user_sentiment:
            raise MessagesNotFound

        view = discord.Embed(
            title="User Sentiment",
            description=USER_SENTIMENT_TEMPLATE.format(
                sentiment=sentiment,
                user=user.mention,
                compound=average_sentiment,
            ),
            timestamp=discord.utils.utcnow(),
        )

        return await interaction.response.send_message(
            embed=view,
            ephemeral=True,
        )

    @contextmenu(name="Show message sentiment")
    async def show_message_sentiment(
        self,
        interaction: discord.Interaction,
        message: discord.Message,
    ) -> None:
        """
        Allow users to view the sentiment analysis of a message using a context menu.

        Generates an embed with the sentiment analysis of a message and sends it to the user.

        The embed contains a text description of the sentiment analysis and a bar chart.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        message : discord.Message
            The message to analyze.
        """
        logger.info(
            "User %s requested sentiment analysis results for message %s.",
            interaction.user.id,
            message.id,
        )

        if self.bot.redis is None:
            return await interaction.response.send_message(
                "This feature is currently unavailable. Please try again later.",
                ephemeral=True,
            )

        if message.guild is None:
            return await interaction.response.send_message(
                "This feature is only available in guilds.",
                ephemeral=True,
            )

        key = key_schema.guild_messages(
            guild_id=message.guild.id,
            message_id=message.id,
        )

        analysis_result = await get_message_sentiment(key, redis=self.bot.redis)

        if analysis_result is None:
            return await interaction.response.send_message(
                "No sentiment analysis found for this message.",
                ephemeral=True,
            )

        color = discord.Color.green() if analysis_result.compound >= 0 else discord.Color.red()

        sentiment = next(
            (
                value
                for key, value in SENTIMENT.items()
                if int(analysis_result.compound * 100) in key
            ),
            "unknown",
        )

        template_vars = {
            **analysis_result.model_dump(),
            "sentiment": sentiment,
        }

        view = discord.Embed(
            title="Message Sentiment",
            description=MESSAGE_SENTIMENT_TEMPLATE.format(**template_vars),
            color=color,
            timestamp=discord.utils.utcnow(),
        )

        chart = plot_sentiment_analysis(message.id, analysis_result)
        chart_file = discord.File(chart, filename="sentiment_analysis.png")
        view.set_image(url="attachment://sentiment_analysis.png")

        return await interaction.response.send_message(
            embed=view,
            file=chart_file,
            ephemeral=True,
        )


async def setup(bot: CourageousCometsBot) -> None:
    """Load the cog."""
    await bot.add_cog(Sentiment(bot))

import logging

from discord import Intents, Object
from discord.ext import commands
from discord.interactions import Interaction

from .settings import BotSettings, settings

logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    """Overriden class for the default discord Bot."""

    def __init__(self, settings: BotSettings) -> None:
        self.settings = settings
        super().__init__(settings.COMMAND_PREFIX, intents=Intents.default())

    async def on_ready(self) -> None:
        """Overriden method on_ready."""
        logger.warning(
            "[bot] syncing commands into server %s",
            self.settings.GUILD_ID,
        )
        await bot.tree.sync(guild=Object(id=settings.GUILD_ID))
        logger.warning("DONE syncing commands!")


bot = Bot(settings)


@bot.tree.command(
    name="jam",
    description="CodeJam Hello World!",
    guild=Object(id=settings.GUILD_ID),
)
async def hello_world(interaction: Interaction) -> None:
    """Says hello world."""
    await interaction.response.send_message("Hello World!")

import logging

from .bot import bot
from .settings import settings


def main() -> None:
    """Run the app."""
    logging.basicConfig(level=logging.INFO)
    bot.run(settings.DISCORD_TOKEN)


if __name__ == "__main__":
    main()

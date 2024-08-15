from collections.abc import Sequence
from sys import exception
from typing import Any, ClassVar, override

import aiohttp
import discord
from aiocache import BaseCache
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.log import get_logger

log = get_logger(__name__)


class Bot(discord.Bot):
    """Bot subclass that holds the state of the application.

    The bot instance is available throughout the application, which makes it
    suitable to store various state variables that are needed in multiple places,
    such as database connections.
    """

    EXTENSIONS: ClassVar[Sequence[str]] = [
        "src.exts.ping",
        "src.exts.error_handler",
        "src.exts.sudo",
        "src.exts.help",
        "src.exts.tvdb_info",
    ]

    def __init__(
        self,
        *args: object,
        http_session: aiohttp.ClientSession,
        db_session: AsyncSession,
        cache: BaseCache,
        **kwargs: object,
    ) -> None:
        """Initialize the bot instance, containing various state variables."""
        super().__init__(*args, **kwargs)
        self.http_session = http_session
        self.db_session = db_session
        self.cache = cache

        self.event(self.on_ready)

    async def on_ready(self) -> None:
        """The `on_ready` event handler."""
        log.info(f"{self.user} is ready and online!")

    def load_all_extensions(self) -> None:
        """Load all of our bot extensions.

        This relies on the `EXTENSIONS` class variable.
        """
        log.info("Loading extensions...")
        self.load_extensions(*self.EXTENSIONS)

    @override
    def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """Log errors raised in commands and events properly, rather than just printing them to stderr."""
        log.exception(f"Unhandled exception in {event_method}", exc_info=exception())

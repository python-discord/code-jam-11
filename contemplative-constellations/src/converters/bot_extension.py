import importlib
import inspect
from typing import override

from discord.ext.commands import Bot, Context, Converter


class ValidBotExtension(Converter[str]):
    """Convert given extension name to a fully qualified path to extension."""

    @staticmethod
    def valid_extension_path(extension_name: str) -> str:
        """Get the fully qualified path to a valid bot extension.

        The `extension_name` can be:
        - A fully qualified path (e.g. 'src.exts.ping'),
        - A suffix component of a fully qualified path (e.g. 'exts.ping', or just 'ping')

          The suffix must still be an entire path component, so while 'ping' is valid, 'pi' or 'ng' is not.

        If the `extension_name` doesn't point to a valid extension a ValueError will be raised.
        """
        extension_name = extension_name.removeprefix("src.exts.").removeprefix("exts.")
        extension_name = f"src.exts.{extension_name}"

        # This could technically be a vulnerability, but this converter can only
        # be used by the bot owner
        try:
            imported = importlib.import_module(extension_name)
        except ModuleNotFoundError:
            raise ValueError(f"Unable to import '{extension_name}'.")

        # If it lacks a setup function, it's not an extension
        if not inspect.isfunction(getattr(imported, "setup", None)):
            raise ValueError(f"'{extension_name}' is not a valid extension.")

        return extension_name

    @override
    async def convert(self, ctx: Context[Bot], argument: str) -> str:
        """Try to match given `argument` to a valid extension within the bot project."""
        return self.valid_extension_path(argument)

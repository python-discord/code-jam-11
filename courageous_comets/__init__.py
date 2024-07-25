import importlib.metadata
import logging

from .client import bot

__all__ = ["bot"]

try:
    __version__ = importlib.metadata.version("courageous_comets")
except importlib.metadata.PackageNotFoundError:
    logging.warning("Could not determine the package version.")
    __version__ = "unknown"

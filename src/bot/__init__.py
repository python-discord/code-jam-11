"""The Bot module provides the main bot classes for EcoCord.

Classes:
    EcoCordClient: The main bot client for EcoCord.
    TestEcoCordClient: A test version of the bot client for development and testing purposes.
"""

from .bot import EcoCordClient
from .test_bot import TestEcoCordClient

__all__ = ["EcoCordClient", "TestEcoCordClient"]

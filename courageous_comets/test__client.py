from typing import Self

import discord
import pytest
from discord.ext import commands
from pytest_mock import MockerFixture, MockType

from .client import bot, intents, logger, on_ready, setup_hook, sync


class MockAsyncContextManager:
    """Mock an asynchronous context manager."""

    async def __aenter__(self, *args, **kwargs) -> Self:  # noqa: ANN002, ANN003
        return self

    async def __aexit__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        pass


@pytest.fixture()
def mock_context(mocker: MockerFixture) -> MockType:
    """Create a mock context for testing."""
    ctx = mocker.Mock(spec=commands.Context)
    ctx.bot = mocker.Mock()
    ctx.bot.tree = mocker.Mock()
    ctx.bot.tree.clear_commands = mocker.Mock()
    ctx.bot.tree.copy_global_to = mocker.Mock()
    ctx.bot.tree.sync = mocker.AsyncMock(return_value=[mocker.Mock()])
    ctx.guild = mocker.Mock()
    ctx.send = mocker.AsyncMock()
    ctx.typing = mocker.MagicMock(MockAsyncContextManager())
    return ctx


def test__bot_has_required_intents() -> None:
    """
    Test whether the bot has the required intents.

    Asserts
    -------
    - The bot has the required intents.
    """
    assert bot.intents == intents


@pytest.mark.asyncio()
async def test__on_ready_logs_message(mocker: MockerFixture) -> None:
    """
    Test whether the on_ready function logs the expected message.

    Asserts
    -------
    - The logger.info function is called with the expected message.
    """
    logger_info = mocker.spy(logger, "info")
    await on_ready()
    logger_info.assert_called_with("Logged in as %s", mocker.ANY)


@pytest.mark.asyncio()
async def test__setup_hook_loads_all_cogs(mocker: MockerFixture) -> None:
    """
    Test whether the setup_hook function loads all cogs from the config file.

    Asserts
    -------
    - The bot.load_extension function is called for each cog in the config file.
    """
    cogs = ["cog1", "cog2", "cog3"]

    mocker.patch("courageous_comets.client.CONFIG", {"cogs": cogs})
    load_extension = mocker.patch("discord.ext.commands.Bot.load_extension")

    await setup_hook()

    for cog in cogs:
        load_extension.assert_any_call(cog)


@pytest.mark.asyncio()
async def test__setup_hook_logs_loaded_cogs(mocker: MockerFixture) -> None:
    """
    Test whether the setup_hook function logs the correct message for each cog.

    Asserts
    -------
    - The logger.info function is called with the correct message for each cog.
    """
    cogs = ["cog1", "cog2", "cog3"]

    mocker.patch("courageous_comets.client.CONFIG", {"cogs": cogs})
    mocker.patch("discord.ext.commands.Bot.load_extension", return_value=None)
    logger_info = mocker.spy(logger, "info")

    await setup_hook()

    for cog in cogs:
        logger_info.assert_any_call("Loaded cog %s", cog)


@pytest.mark.asyncio()
async def test__setup_hook_logs_exception_on_extension_error(mocker: MockerFixture) -> None:
    """
    Test whether the setup_hook function logs an exception when an ExtensionError is raised.

    Asserts
    -------
    - The logger.exception function is called when an ExtensionError is raised.
    """
    mocker.patch("courageous_comets.client.CONFIG", {"cogs": ["cog1"]})
    expected = commands.ExtensionError(name="cog1")
    mocker.patch("discord.ext.commands.Bot.load_extension", side_effect=expected)

    logger_exception = mocker.spy(logger, "exception")

    await setup_hook()

    logger_exception.assert_called_with("Failed to load cog %s", "cog1", exc_info=expected)


@pytest.mark.asyncio()
async def test__sync_syncs_to_current_guild(mock_context: MockType) -> None:
    """
    Test whether the sync command syncs to the current guild.

    Asserts
    -------
    - The bot.sync function is called with the expected parameters.
    - The ctx.send function is called with the expected message.
    """
    await sync(mock_context, [], "~")

    mock_context.bot.tree.sync.assert_called_with(guild=mock_context.guild)
    mock_context.send.assert_called_with(
        f"Synced {len(mock_context.bot.tree.sync.return_value)} command(s) to the current guild.",
    )


@pytest.mark.asyncio()
async def test__sync_syncs_to_global_scope(mock_context: MockType) -> None:
    """
    Test whether the sync command syncs to the global scope.

    Asserts
    -------
    - The bot.sync function is called with the expected parameters.
    - The ctx.send function is called with the expected message
    """
    await sync(mock_context, [], "*")

    mock_context.bot.tree.sync.to_have_been_called_with()
    mock_context.send.assert_called_with(
        f"Synced {len(mock_context.bot.tree.sync.return_value)} command(s) globally.",
    )


@pytest.mark.asyncio()
async def test__sync_removes_non_global_commands(mock_context: MockType) -> None:
    """
    Test whether the sync command removes non-global commands.

    Asserts
    -------
    - The bot.tree.clear_commands function is called with the expected parameters.
    - The bot.sync function is called with the expected parameters
    - The ctx.send function is called with the expected message
    """
    await sync(mock_context, [], "^")

    mock_context.bot.tree.clear_commands.assert_called_with(guild=mock_context.guild)
    mock_context.bot.tree.sync.assert_called_with(guild=mock_context.guild)
    mock_context.send.assert_called_with("Synced 0 command(s) to the current guild.")


@pytest.mark.asyncio()
async def test__sync_syncs_to_given_guilds(
    mocker: MockerFixture,
    mock_context: MockType,
) -> None:
    """
    Test whether the sync command syncs to the given guilds.

    Asserts
    -------
    - The bot.sync function is called with the expected parameters.
    - The ctx.send function is called with the expected message.
    """
    guilds = [mocker.Mock(), mocker.Mock()]
    await sync(mock_context, guilds)

    for guild in guilds:
        mock_context.bot.tree.sync.assert_any_call(guild=guild)

    mock_context.send.assert_called_with(f"Synced the tree to {len(guilds)}/{len(guilds)}.")


@pytest.mark.asyncio()
async def test__sync_logs_exception_on_http_exception(
    mocker: MockerFixture,
    mock_context: MockType,
) -> None:
    """
    Test whether the sync command handles an HTTPException correctly.

    Asserts
    -------
    - The logger.exception function is called when an HTTPException is raised.
    - The ctx.send function is called with the expected message.
    """
    guilds = [mocker.Mock(), mocker.Mock()]
    expected = discord.HTTPException(response=mocker.Mock(), message="Failed to sync")
    mock_context.bot.tree.sync.side_effect = expected

    logger_exception = mocker.spy(logger, "exception")

    await sync(mock_context, guilds)

    for guild in guilds:
        logger_exception.assert_any_call("Failed to sync to guild %s", guild, exc_info=expected)

    mock_context.send.assert_called_with(f"Synced the tree to 0/{len(guilds)}.")

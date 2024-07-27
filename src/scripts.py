"""Utility scripts for running various commands and development tasks.

This module provides functions to execute different commands and development
workflows using Poetry. It includes functions for formatting, linting, and
running different versions of the application.
"""

import os
import signal
import subprocess
from contextlib import suppress
from pathlib import Path


def run_command(command: list[str]) -> None:
    """Run a command in a subprocess with proper environment setup and signal handling.

    Args:
    ----
        command (list[str]): The command to run as a list of strings.

    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.resolve())
    # Run the process and make sure to terminate it properly
    process = subprocess.Popen(command, env=env)
    try:
        process.communicate()
    except KeyboardInterrupt:
        os.kill(process.pid, signal.SIGINT)
    finally:
        with suppress(ProcessLookupError):
            os.kill(process.pid, signal.SIGTERM)


def format() -> None:
    """Run the 'ruff format' command using Poetry."""
    run_command(["poetry", "run", "ruff", "format"])


def lint() -> None:
    """Run the 'ruff check' command using Poetry."""
    run_command(["poetry", "run", "ruff", "check"])


def run() -> None:
    """Run the main application using Poetry."""
    run_command(["poetry", "run", "python", "src/app.py"])


def run_interactive() -> None:
    """Run the interactive version of the application using Poetry."""
    run_command(["poetry", "run", "python", "src/app.py", "--interactive"])


def run_discord_test() -> None:
    """Run the Discord test version of the application using Poetry."""
    run_command(["poetry", "run", "python", "src/app.py", "--test"])


def run_gifs() -> None:
    """Run the GIF generation version of the application using Poetry."""
    run_command(["poetry", "run", "python", "src/app.py", "--gifs"])


def dev() -> None:
    """Run format, lint, and the main application in sequence."""
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run"])


def dev_interactive() -> None:
    """Run format, lint, and the interactive version of the application."""
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run-interactive"])


def dev_discord_test() -> None:
    """Run format, lint, and the Discord test version of the application."""
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run-test"])


def dev_gifs() -> None:
    """Run format, lint, and the GIF generation version of the application."""
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run-gifs"])

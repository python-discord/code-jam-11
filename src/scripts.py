import os
import subprocess
from pathlib import Path


def run_command(command: list[str]) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.resolve())
    subprocess.run(command, env=env, check=True)


def format() -> None:
    run_command(["poetry", "run", "ruff", "format"])


def lint() -> None:
    run_command(["poetry", "run", "ruff", "check"])


def dev() -> None:
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run"])


def dev_interactive() -> None:
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run-interactive"])


def dev_discord_test() -> None:
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run-discord-test"])


def dev_gifs() -> None:
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run-gifs"])

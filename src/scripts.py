import os
import signal
import subprocess
from contextlib import suppress
from pathlib import Path


def run_command(command: list[str]) -> None:
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
    run_command(["poetry", "run", "run-test"])


def dev_gifs() -> None:
    run_command(["poetry", "run", "format"])
    run_command(["poetry", "run", "lint"])
    run_command(["poetry", "run", "run-gifs"])

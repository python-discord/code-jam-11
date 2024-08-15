import asyncio
import sys
import time
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

from bot import EcoCordClient, TestEcoCordClient
from ecosystem import EcosystemManager


async def run_discord_bot(test_mode: bool = True) -> None:
    """Run the Discord bot in either test or production mode.

    Args:
    ----
        test_mode (bool): If True, run in test mode with TestEcoCordClient. Default is True.

    Raises:
    ------
        Exception: Any unhandled exception during bot execution.

    """
    loop = asyncio.get_event_loop()
    client = TestEcoCordClient() if test_mode else EcoCordClient()

    try:
        await client.run_bot()
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down...")
    except Exception:
        raise
    finally:
        print("Cleaning up...")
        await client.stop_all_ecosystems()
        await client.close()
        await loop.shutdown_asyncgens()


def run_gif_generator(duration: float | None = None) -> Generator[tuple[str, float], None, None]:
    """Generate GIFs of the ecosystem for a specified duration.

    Args:
    ----
        duration (float | None): Duration in seconds to generate GIFs. If None, run indefinitely.

    Yields:
    ------
        tuple[str, float]: A tuple containing GIF data (bytes) and timestamp.

    """
    manager = EcosystemManager(generate_gifs=True)
    manager.start(show_controls=False)

    start_time = time.time()
    try:
        while duration is None or time.time() - start_time < duration:
            gif_data = manager.get_latest_gif()
            if gif_data:
                yield gif_data
            time.sleep(0.01)
    finally:
        manager.stop()


def run_pygame(show_controls: bool = True, generate_gifs: bool = False) -> EcosystemManager:
    """Run the ecosystem simulation using Pygame.

    Args:
    ----
        show_controls (bool): If True, display simulation controls. Default is True.
        generate_gifs (bool): If True, generate GIFs of the simulation. Default is False.

    Returns:
    -------
        EcosystemManager: The initialized and running EcosystemManager instance.

    """
    manager = EcosystemManager(generate_gifs=generate_gifs)
    manager.start(show_controls=show_controls)
    return manager


def main() -> None:
    """Run the main Discord bot in production mode."""
    print("Running with Discord integration...")
    asyncio.run(run_discord_bot(test_mode=False))


def main_interactive() -> None:
    """Run the ecosystem simulation in interactive mode with Pygame controls."""
    print("Running in interactive mode...")
    manager = run_pygame(show_controls=True, generate_gifs=False)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        manager.stop()


def main_discord_test() -> None:
    """Run the Discord bot in test mode."""
    print("[Test mode] Running with fake Discord integration...")
    asyncio.run(run_discord_bot(test_mode=True))


def main_gifs() -> None:
    """Generate and save GIFs of the ecosystem simulation for a fixed duration."""
    print("Running in GIF generation mode...")
    gif_dir = Path("ecosystem_gifs")
    gif_dir.mkdir(exist_ok=True)

    for gif_bytes, timestamp in run_gif_generator(duration=180):
        filename = f"ecosystem_{datetime.fromtimestamp(timestamp, tz=UTC).strftime('%Y%m%d_%H%M%S')}.gif"
        filepath = gif_dir / filename

        filepath.write_bytes(gif_bytes)

        print(f"New GIF saved: {filepath}")


if __name__ == "__main__":
    if "--interactive" in sys.argv or "-i" in sys.argv:
        main_interactive()
    elif "--test" in sys.argv:
        main_discord_test()
    elif "--gifs" in sys.argv:
        main_gifs()
    else:
        main()

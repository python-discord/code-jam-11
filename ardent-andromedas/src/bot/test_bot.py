import asyncio
import random
import traceback
from contextlib import suppress
from datetime import UTC, datetime

from .bot import EcoCordClient
from .discord_event import DiscordEvent, FakeUser


class TestEcoCordClient(EcoCordClient):
    """A test client for EcoCordClient that generates fake Discord events."""

    def __init__(self) -> None:
        """Initialize the TestEcoCordClient with fake users, channels, and guild."""
        super().__init__()
        self.fake_users = [FakeUser(id=i, display_name=f"User{i}") for i in range(1, 6)]
        self.fake_channels = [type("Channel", (), {"id": i, "name": f"Channel{i}"})() for i in range(1, 4)]
        self.fake_guild = type("Guild", (), {"id": 1, "name": "TestGuild"})()
        self.fake_events_task = None

    async def on_ready(self) -> None:
        """Event receiver for when the client is ready. Starts generating fake events."""
        print("Test client ready. Generating fake events...")
        self.fake_events_task = asyncio.create_task(self.generate_fake_events())

    async def generate_fake_events(self) -> None:
        """Continuously generate fake events (messages, reactions, or typing)."""
        while True:
            await asyncio.sleep(random.uniform(0.5, 2.0))
            event_type = random.choice(["message", "reaction", "typing"])

            if event_type == "message":
                await self.generate_fake_message()
            elif event_type == "reaction":
                await self.generate_fake_reaction()
            else:
                await self.generate_fake_typing()

    async def generate_fake_message(self) -> None:
        """Generate and process a fake message event."""
        user = random.choice(self.fake_users)
        channel = random.choice(self.fake_channels)
        event = DiscordEvent(
            type="message",
            timestamp=datetime.now(UTC),
            guild=self.fake_guild,
            channel=channel,
            user=user,
            content=f"Fake message {random.randint(1, 1000)}",
        )
        await self.process_event(event)

    async def generate_fake_reaction(self) -> None:
        """Generate and process a fake reaction event."""
        channel = random.choice(self.fake_channels)
        event = DiscordEvent(
            type="reaction",
            timestamp=datetime.now(UTC),
            guild=self.fake_guild,
            channel=channel,
            user=random.choice(self.fake_users),
            content=f"👍 added on Fake message {random.randint(1, 1000)}",
        )
        await self.process_event(event)

    async def generate_fake_typing(self) -> None:
        """Generate and process a fake typing event."""
        channel = random.choice(self.fake_channels)
        event = DiscordEvent(
            type="typing",
            timestamp=datetime.now(UTC),
            guild=self.fake_guild,
            channel=channel,
            user=random.choice(self.fake_users),
            content="User is typing",
        )
        await self.process_event(event)

    async def run_bot(self) -> None:
        """Run the test bot, generating fake events until stopped or an error occurs."""
        print("Starting test bot...")
        self.ready = True
        await self.on_ready()
        try:
            while True:
                if self.fake_events_task and self.fake_events_task.done():
                    # This will raise the exception if there is one
                    await self.fake_events_task
                # Short sleep to prevent busy-waiting
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print("Bot execution cancelled.")
        except Exception:
            # Re-raise the exception after printing the stack trace
            traceback.print_exc()
            raise
        finally:
            await self.stop_bot()

    async def stop_bot(self) -> None:
        """Stop the bot by cancelling the fake events task."""
        if self.fake_events_task:
            self.fake_events_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.fake_events_task

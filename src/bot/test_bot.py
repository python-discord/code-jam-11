import asyncio
import random
from contextlib import suppress
from datetime import UTC, datetime

from .bot import DiscordEvent, EcoCordClient


class TestEcoCordClient(EcoCordClient):
    def __init__(self) -> None:
        super().__init__()
        self.fake_users = [{"id": i, "name": f"User{i}"} for i in range(1, 6)]
        self.fake_channels = [{"id": i, "name": f"Channel{i}"} for i in range(1, 4)]
        self.fake_guild = {"id": 1, "name": "TestGuild"}
        self.fake_events_task = None

    async def on_ready(self) -> None:
        print("Test client ready. Generating fake events...")
        self.fake_events_task = asyncio.create_task(self.generate_fake_events())

    async def generate_fake_events(self) -> None:
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
        event = DiscordEvent(
            type="message",
            timestamp=datetime.now(UTC),
            guild=self.fake_guild,
            channel=random.choice(self.fake_channels),
            user=random.choice(self.fake_users),
            content=f"Fake message {random.randint(1, 1000)}",
        )
        await self.process_event(event)

    async def generate_fake_reaction(self) -> None:
        event = DiscordEvent(
            type="reaction",
            timestamp=datetime.now(UTC),
            guild=self.fake_guild,
            channel=random.choice(self.fake_channels),
            user=random.choice(self.fake_users),
            content=f"👍 added on Fake message {random.randint(1, 1000)}",
        )
        await self.process_event(event)

    async def generate_fake_typing(self) -> None:
        event = DiscordEvent(
            type="typing",
            timestamp=datetime.now(UTC),
            guild=self.fake_guild,
            channel=random.choice(self.fake_channels),
            user=random.choice(self.fake_users),
            content="User is typing",
        )
        await self.process_event(event)

    async def run_bot(self) -> None:
        print("Starting test bot...")
        self.ready = True
        await self.on_ready()
        try:
            # Run for a limited time or until interrupted
            await asyncio.sleep(3600)
        finally:
            await self.stop_bot()

    async def stop_bot(self) -> None:
        if self.fake_events_task:
            self.fake_events_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.fake_events_task

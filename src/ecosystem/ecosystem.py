import atexit
import contextlib
import io
import multiprocessing
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from .shared_numpy_array import SharedNumpyArray

# Hide pygame welcome message
with contextlib.redirect_stdout(None):
    import pygame

import random

from PIL import Image

from bot.discord_event import DiscordEvent

from .bird import Bird
from .frog import Frog
from .plant import Plant
from .snake import Snake


class Ecosystem:
    """Represents the ecosystem simulation environment.

    This class manages the overall ecosystem, including various entities like plants, frogs, snakes, and birds.
    It handles the simulation logic, drawing, and user interface elements.
    """

    def __init__(
        self,
        width: int,
        height: int,
        generate_gifs: bool = False,
        gif_duration: int = 5,
        fps: int = 30,
        interactive: bool = True,
    ) -> None:
        """Initialize the Ecosystem.

        Args:
        ----
            width (int): Width of the ecosystem surface.
            height (int): Height of the ecosystem surface.
            generate_gifs (bool): Whether to generate GIFs of the simulation.
            gif_duration (int): Duration of each GIF in seconds.
            fps (int): Frames per second for the simulation.
            interactive (bool): Whether the ecosystem is interactive or not.

        """
        self.width = width
        self.height = height
        self.activity = 1
        self.elapsed_time = 0
        self.surface = pygame.Surface((width, height))

        self.sky_colors = [
            (200, 200, 200),  # Barren gray
            (135, 206, 235),  # Lush blue
        ]
        self.ground_colors = [
            (210, 180, 140),  # Barren tan
            (34, 139, 34),  # Lush green
        ]

        self.plants = []
        self.frogs = []
        self.snakes = []
        self.birds = []

        self.font = None
        self.activity_slider = None
        self.spawn_plant_button = None
        self.spawn_frog_button = None
        self.spawn_snake_button = None
        self.spawn_bird_button = None
        self.reset_button = None

        self.generate_gifs = generate_gifs
        self.fps = fps
        self.interactive = interactive

        if self.generate_gifs:
            self.gif_duration = gif_duration
            self.frames_per_gif = self.fps * self.gif_duration
            self.frame_count = 0
            self.shared_frames = SharedNumpyArray((self.frames_per_gif, width, height, 3))
            self.current_frame_index = multiprocessing.Value("i", 0)
            self.frame_count_queue = multiprocessing.Queue()
            self.gif_info_queue = multiprocessing.Queue()
            self.gif_process = multiprocessing.Process(
                target=self._gif_generation_process,
                args=(
                    self.shared_frames,
                    self.current_frame_index,
                    self.frame_count_queue,
                    self.gif_info_queue,
                    self.fps,
                ),
            )
            self.gif_process.start()

        atexit.register(self.cleanup)

    def setup_ui(self) -> None:
        """Set up the user interface elements for the ecosystem."""
        self.font = pygame.font.Font(None, 24)

        button_width = 120
        button_height = 30
        button_spacing = 10
        top_margin = 20
        left_margin = 20

        self.activity_slider = pygame.Rect(left_margin, top_margin, 200, 20)

        button_y = top_margin + self.activity_slider.height + button_spacing

        self.spawn_plant_button = Button(
            left_margin,
            button_y,
            button_width,
            button_height,
            "Spawn Plant",
            (0, 255, 0),
            (0, 0, 0),
            self.font,
        )

        self.spawn_frog_button = Button(
            left_margin + button_width + button_spacing,
            button_y,
            button_width,
            button_height,
            "Spawn Frog",
            (0, 0, 255),
            (255, 255, 255),
            self.font,
        )

        self.spawn_snake_button = Button(
            left_margin + (button_width + button_spacing) * 2,
            button_y,
            button_width,
            button_height,
            "Spawn Snake",
            (255, 200, 0),
            (0, 0, 0),
            self.font,
        )

        self.spawn_bird_button = Button(
            left_margin + (button_width + button_spacing) * 3,
            button_y,
            button_width,
            button_height,
            "Spawn Bird",
            (100, 100, 255),
            (255, 255, 255),
            self.font,
        )

        self.reset_button = Button(
            left_margin + (button_width + button_spacing) * 4,
            button_y,
            button_width,
            button_height,
            "Reset",
            (255, 0, 0),
            (255, 255, 255),
            self.font,
        )

    def update(self, delta: float) -> None:
        """Update the state of the ecosystem.

        Args:
        ----
            delta (float): Time elapsed since the last update.

        """
        self.elapsed_time += delta

        for plant in self.plants:
            plant.update(delta, self.activity)

        for frog in self.frogs:
            frog.update(delta, self.activity)

        for snake in self.snakes:
            snake.update(delta, self.activity)

        for bird in self.birds:
            bird.update(delta, self.activity)

        if self.interactive:
            self._handle_standard_spawning(delta)

        self._clean_up_entities()

    def _handle_standard_spawning(self, delta: float) -> None:
        """Handle the standard spawning of entities based on activity level.

        Args:
        ----
            delta (float): Time elapsed since the last update.

        """
        if random.random() < self.activity * delta:
            self.spawn_plant()

        if random.random() < self.activity * delta * 0.5:
            self.spawn_frog()

        if random.random() < self.activity * delta * 0.3:
            self.spawn_snake()

        if random.random() < self.activity * delta * 0.4:
            self.spawn_bird()

    def _clean_up_entities(self) -> None:
        """Remove dead entities from the ecosystem."""
        self.plants = [plant for plant in self.plants if plant.alive]
        self.frogs = [frog for frog in self.frogs if frog.alive]
        self.snakes = [snake for snake in self.snakes if snake.alive]
        self.birds = [bird for bird in self.birds if bird.alive]

    def draw(self) -> pygame.Surface:
        """Draw the current state of the ecosystem.

        Returns
        -------
            pygame.Surface: The surface with the drawn ecosystem.

        """
        sky_color = self.interpolate_color(self.sky_colors[0], self.sky_colors[1], self.activity)
        self.surface.fill(sky_color)

        ground_color = self.interpolate_color(self.ground_colors[0], self.ground_colors[1], self.activity)
        pygame.draw.rect(self.surface, ground_color, (0, self.height * 0.7, self.width, self.height * 0.3))

        for plant in self.plants:
            plant.draw(self.surface)

        for frog in self.frogs:
            frog.draw(self.surface)

        for snake in self.snakes:
            snake.draw(self.surface)

        for bird in self.birds:
            bird.draw(self.surface)

        return self.surface

    def post_update(self) -> None:
        """Perform post-update operations, such as frame capturing for GIF generation."""
        if self.generate_gifs:
            frame = pygame.surfarray.array3d(self.surface)
            frames = self.shared_frames.get_array()
            index = self.current_frame_index.value
            frames[index] = frame
            self.current_frame_index.value = (index + 1) % self.frames_per_gif
            self.frame_count += 1

            if self.frame_count % self.frames_per_gif == 0:
                (self.frame_count_queue.put(self.frame_count))

    def interpolate_color(
        self, color1: tuple[int, int, int], color2: tuple[int, int, int], t: float
    ) -> tuple[int, int, int]:
        """Interpolate between two colors.

        Args:
        ----
            color1 (tuple[int, int, int]): The first color.
            color2 (tuple[int, int, int]): The second color.
            t (float): Interpolation factor between 0 and 1.

        Returns:
        -------
            tuple[int, int, int]: The interpolated color.

        """
        return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2, strict=False))

    def spawn_plant(self) -> None:
        """Spawn a new plant in the ecosystem."""
        self.plants.append(Plant(random.randint(0, self.width), self.height * 0.7))

    def spawn_frog(self) -> None:
        """Spawn a new frog in the ecosystem."""
        new_frog = Frog(random.randint(0, self.width), self.height - 20, self.width, self.height)
        new_frog.spawn()
        self.frogs.append(new_frog)

    def spawn_snake(self) -> None:
        """Spawn a new snake in the ecosystem."""
        new_snake = Snake(random.randint(0, self.width), self.height * 0.7, self.width, self.height)
        new_snake.spawn()
        self.snakes.append(new_snake)

    def spawn_bird(self) -> None:
        """Spawn a new bird in the ecosystem."""
        new_bird = Bird(self.width, self.height)
        new_bird.spawn()
        self.birds.append(new_bird)

    def reset(self) -> None:
        """Reset the ecosystem to its initial state."""
        self.plants.clear()
        self.frogs.clear()
        self.snakes.clear()
        self.birds.clear()
        self.activity = 1
        self.elapsed_time = 0

    @staticmethod
    def _gif_generation_process(
        shared_frames: SharedNumpyArray,
        current_frame_index: multiprocessing.Value,
        frame_count_queue: multiprocessing.Queue,
        gif_info_queue: multiprocessing.Queue,
        fps: int,
    ) -> None:
        """Process for generating GIFs from captured frames.

        Args:
        ----
            shared_frames (SharedNumpyArray): Shared array containing frame data.
            current_frame_index (multiprocessing.Value): Current frame index.
            frame_count_queue (multiprocessing.Queue): Queue for frame count information.
            gif_info_queue (multiprocessing.Queue): Queue for generated GIF information.
            fps (int): Frames per second for the GIF.

        """
        frames = shared_frames.get_array()

        def optimize_frame(frame: np.ndarray) -> Image.Image:
            return Image.fromarray(frame.transpose(1, 0, 2)).quantize(method=Image.MEDIANCUT, colors=256)

        with ThreadPoolExecutor() as executor:
            while True:
                frame_count = frame_count_queue.get()
                if frame_count is None:
                    break

                start_index = current_frame_index.value
                ordered_frames = np.roll(frames, -start_index, axis=0)

                optimized_frames = list(executor.map(optimize_frame, ordered_frames))

                duration = int(1000 / fps)

                with io.BytesIO() as gif_buffer:
                    optimized_frames[0].save(
                        gif_buffer,
                        format="GIF",
                        save_all=True,
                        append_images=optimized_frames[1:],
                        optimize=False,
                        duration=[duration] * (len(optimized_frames) - 1) + [15000],
                        loop=0,
                    )

                    gif_data = gif_buffer.getvalue()

                gif_info_queue.put((gif_data, time.time()))

    def cleanup(self) -> None:
        """Clean up resources used by the ecosystem."""
        print("Cleaning up Ecosystem...")
        if pygame.get_init():
            pygame.quit()
        if hasattr(self, "gif_process"):
            # Signal to stop the gif generation process
            self.frame_count_queue.put(None)

            self.gif_process.join()


class Button:
    """Represents a clickable button in the user interface."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: tuple[int, int, int],
        text_color: tuple[int, int, int],
        font: pygame.font.Font,
    ) -> None:
        """Initialize a Button.

        Args:
        ----
            x (int): X-coordinate of the button.
            y (int): Y-coordinate of the button.
            width (int): Width of the button.
            height (int): Height of the button.
            text (str): Text to display on the button.
            color (tuple[int, int, int]): Color of the button.
            text_color (tuple[int, int, int]): Color of the text.
            font (pygame.font.Font): Font for the button text.

        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = font

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the button on the given surface.

        Args:
        ----
            surface (pygame.Surface): Surface to draw the button on.

        """
        pygame.draw.rect(surface, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def is_clicked(self, position: tuple[int, int]) -> bool:
        """Check if the button is clicked.

        Args:
        ----
            position (tuple[int, int]): Position of the mouse click.

        Returns:
        -------
            bool: True if the button is clicked, False otherwise.

        """
        return self.rect.collidepoint(position)


class EcosystemManager:
    """Manages the ecosystem simulation and handles user interactions."""

    def __init__(
        self, width: int = 800, height: int = 600, generate_gifs: bool = False, fps: int = 30, interactive: bool = True
    ) -> None:
        """Initialize the EcosystemManager.

        Args:
        ----
            width (int): Width of the ecosystem window.
            height (int): Height of the ecosystem window.
            generate_gifs (bool): Whether to generate GIFs of the simulation.
            fps (int): Frames per second for the simulation.
            interactive (bool): Whether the ecosystem is interactive or not.

        """
        self.width = width
        self.height = height
        self.generate_gifs = generate_gifs
        self.fps = fps
        self.interactive = interactive
        self.process = None
        self.command_queue = multiprocessing.Queue()
        self.gif_queue = multiprocessing.Queue()
        self.running = False

        if not self.interactive:
            self.user_frogs = {}  # Dictionary to store user frogs
            self.last_activity = {}  # Dictionary to store last activity time for each user

    def start(self, show_controls: bool = True) -> None:
        """Start the ecosystem simulation.

        Args:
        ----
            show_controls (bool): Whether to show UI controls.

        """
        if self.process and self.process.is_alive():
            return

        self.running = True
        self.process = multiprocessing.Process(target=self._run_ecosystem, args=(show_controls,))
        self.process.start()

    def stop(self) -> None:
        """Stop the ecosystem simulation."""
        self.running = False
        self.command_queue.put(("stop", None))
        if self.process:
            self.process.join()

    def _run_ecosystem(self, show_controls: bool) -> None:
        """Run the ecosystem simulation loop.

        Args:
        ----
            show_controls (bool): Whether to show UI controls.

        """
        pygame.init()
        ecosystem = Ecosystem(
            self.width, self.height, generate_gifs=self.generate_gifs, fps=self.fps, interactive=self.interactive
        )
        ecosystem.setup_ui()

        if self.interactive:
            screen = pygame.display.set_mode((ecosystem.width, ecosystem.height))
            pygame.display.set_caption(f"Ecosystem Visualization {multiprocessing.current_process().name}")
        else:
            # Create a hidden surface for rendering
            screen = pygame.Surface((ecosystem.width, ecosystem.height))

        clock = pygame.time.Clock()

        while self.running:
            delta = clock.tick(self.fps) / 1000.0

            if self.interactive:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif show_controls and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self._handle_mouse_click(ecosystem, event.pos)

            ecosystem.update(delta)
            screen.blit(ecosystem.draw(), (0, 0))
            ecosystem.post_update()

            if self.interactive and show_controls:
                self._draw_controls(ecosystem, screen)

            if self.interactive:
                pygame.display.flip()

            if ecosystem.generate_gifs and not ecosystem.gif_info_queue.empty():
                gif_data, timestamp = ecosystem.gif_info_queue.get()
                self.gif_queue.put((gif_data, timestamp))

            # Check for commands from the main process
            while not self.command_queue.empty():
                command, args = self.command_queue.get()
                if command == "stop":
                    self.running = False
                elif command == "process_event":
                    self._process_event(ecosystem, args)

        pygame.quit()
        ecosystem.cleanup()

    def _handle_mouse_click(self, ecosystem: Ecosystem, pos: tuple[int, int]) -> None:
        """Handle mouse click events in the ecosystem.

        Args:
        ----
            ecosystem (Ecosystem): The ecosystem instance.
            pos (tuple[int, int]): Position of the mouse click.

        """
        if ecosystem.activity_slider.collidepoint(pos):
            ecosystem.activity = (pos[0] - ecosystem.activity_slider.x) / ecosystem.activity_slider.width
        elif ecosystem.spawn_plant_button.is_clicked(pos):
            ecosystem.spawn_plant()
        elif ecosystem.spawn_frog_button.is_clicked(pos):
            ecosystem.spawn_frog()
        elif ecosystem.spawn_snake_button.is_clicked(pos):
            ecosystem.spawn_snake()
        elif ecosystem.spawn_bird_button.is_clicked(pos):
            ecosystem.spawn_bird()
        elif ecosystem.reset_button.is_clicked(pos):
            ecosystem.reset()

    def _draw_controls(self, ecosystem: Ecosystem, screen: pygame.Surface) -> None:
        """Draw UI controls on the screen.

        Args:
        ----
            ecosystem (Ecosystem): The ecosystem instance.
            screen (pygame.Surface): Surface to draw the controls on.

        """
        pygame.draw.rect(screen, (200, 200, 200), ecosystem.activity_slider)
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (
                ecosystem.activity_slider.x,
                ecosystem.activity_slider.y,
                ecosystem.activity_slider.width * ecosystem.activity,
                ecosystem.activity_slider.height,
            ),
        )

        ecosystem.spawn_plant_button.draw(screen)
        ecosystem.spawn_frog_button.draw(screen)
        ecosystem.spawn_snake_button.draw(screen)
        ecosystem.spawn_bird_button.draw(screen)
        ecosystem.reset_button.draw(screen)

        activity_text = ecosystem.font.render(f"Activity: {ecosystem.activity:.2f}", True, (0, 0, 0))
        screen.blit(activity_text, (ecosystem.activity_slider.x, ecosystem.activity_slider.y - 20))

        stats_text = ecosystem.font.render(
            f"Plants: {len(ecosystem.plants)} | Frogs: {len(ecosystem.frogs)} | Snakes: {len(ecosystem.snakes)} | "
            f"Birds: {len(ecosystem.birds)}",
            True,
            (0, 0, 0),
        )
        screen.blit(stats_text, (25, ecosystem.activity_slider.y + 70))

    def process_event(self, event: DiscordEvent) -> None:
        """Process a Discord event in the ecosystem.

        Args:
        ----
            event (DiscordEvent): The Discord event to process.

        """
        self.command_queue.put(("process_event", event))

    def _process_event(self, ecosystem: Ecosystem, event: DiscordEvent) -> None:
        """Process a Discord event within the ecosystem process.

        Args:
        ----
            ecosystem (Ecosystem): The ecosystem instance.
            event (DiscordEvent): The Discord event to process.

        """
        if not self.interactive:
            current_time = time.time()
            user_id = event.user.id

            if event.type in ("typing", "message"):
                self._handle_user_activity(ecosystem, user_id, current_time, event.type == "typing")

            self._remove_inactive_users(ecosystem, current_time)

    def _handle_user_activity(self, ecosystem: Ecosystem, user_id: int, current_time: float, is_typing: bool) -> None:
        """Handle user activity in the ecosystem.

        Args:
        ----
            ecosystem (Ecosystem): The ecosystem instance.
            user_id (int): ID of the user.
            current_time (float): Current timestamp.
            is_typing (bool): Whether the user is typing.

        """
        if user_id not in self.user_frogs:
            self._spawn_new_frog(ecosystem, user_id)
        elif is_typing:
            self.user_frogs[user_id].move()

        self.last_activity[user_id] = current_time

    def _spawn_new_frog(self, ecosystem: Ecosystem, user_id: int) -> None:
        """Spawn a new frog for a user.

        Args:
        ----
            ecosystem (Ecosystem): The ecosystem instance.
            user_id (int): ID of the user.

        """
        new_frog = Frog(
            random.randint(0, ecosystem.width),
            ecosystem.height - 20,
            ecosystem.width,
            ecosystem.height,
        )
        new_frog.spawn()
        self.user_frogs[user_id] = new_frog
        ecosystem.frogs.append(new_frog)

    def _remove_inactive_users(self, ecosystem: Ecosystem, current_time: float) -> None:
        """Remove inactive users from the ecosystem.

        Args:
        ----
            ecosystem (Ecosystem): The ecosystem instance.
            current_time (float): Current timestamp.

        """
        one_minute = 60
        inactive_users = [
            user_id for user_id, last_time in self.last_activity.items() if current_time - last_time > one_minute
        ]
        for user_id in inactive_users:
            self._remove_user(ecosystem, user_id)

    def _remove_user(self, ecosystem: Ecosystem, user_id: int) -> None:
        """Remove a user from the ecosystem.

        Args:
        ----
            ecosystem (Ecosystem): The ecosystem instance.
            user_id (int): ID of the user to remove.

        """
        if user_id in self.user_frogs:
            frog = self.user_frogs.pop(user_id)
            ecosystem.frogs.remove(frog)
        self.last_activity.pop(user_id, None)

    def get_latest_gif(self) -> tuple[bytes, float] | None:
        """Get the latest generated GIF.

        Returns
        -------
            tuple[bytes, float] | None: Tuple containing GIF data and timestamp, or None if no GIF is available.

        """
        if not self.gif_queue.empty():
            return self.gif_queue.get()
        return None

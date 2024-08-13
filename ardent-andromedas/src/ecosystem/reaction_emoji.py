import io
import random

import pygame
from PIL import Image


class ReactionEmoji:
    """Represents an emoji reaction that appears and animates on the screen."""

    def __init__(self, screen_width: int, screen_height: int, image_data: bytes, duration: float = 5.0) -> None:
        """Initialize a ReactionEmoji instance.

        Args:
        ----
            screen_width (int): Width of the screen.
            screen_height (int): Height of the screen.
            image_data (bytes): Raw image data for the emoji.
            duration (float, optional): Duration of the emoji animation in seconds. Defaults to 5.0.

        """
        self.x = random.randint(0, screen_width)
        self.y = random.randint(0, screen_height)
        self.velocity_x = random.uniform(-100, 100)
        self.velocity_y = random.uniform(-100, 100)
        self.opacity = 255
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = self._create_pygame_image(image_data)
        self.duration = duration
        self.time_left = duration
        self.original_size = self.image.get_size()
        self.current_size = self.original_size

    def _create_pygame_image(self, image_data: bytes) -> pygame.Surface:
        pil_image = Image.open(io.BytesIO(image_data))
        pil_image = pil_image.convert("RGBA")
        return pygame.image.fromstring(pil_image.tobytes(), pil_image.size, pil_image.mode)

    def update(self, delta: float) -> None:
        self.time_left -= delta
        progress = self.time_left / self.duration

        # Update position
        self.x += self.velocity_x * delta
        self.y += self.velocity_y * delta

        # Bounce off screen edges
        if self.x < 0 or self.x > self.screen_width:
            self.velocity_x *= -1
        if self.y < 0 or self.y > self.screen_height:
            self.velocity_y *= -1

        # Update size and opacity
        self.current_size = (int(self.original_size[0] * progress), int(self.original_size[1] * progress))
        self.opacity = int(255 * progress)

    def draw(self, surface: pygame.Surface) -> None:
        if self.current_size[0] > 0 and self.current_size[1] > 0:
            scaled_image = pygame.transform.scale(self.image, self.current_size)
            scaled_image.set_alpha(self.opacity)
            surface.blit(
                scaled_image, (int(self.x) - self.current_size[0] // 2, int(self.y) - self.current_size[1] // 2)
            )

    def is_expired(self) -> bool:
        return self.time_left <= 0

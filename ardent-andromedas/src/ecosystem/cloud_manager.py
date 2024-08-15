import os
import random
from pathlib import Path

import pygame


class Cloud:
    """Represents a cloud object in the game."""

    def __init__(self, image_path: str, speed: float, target_width: int, target_height: int) -> None:
        """Initialize the Cloud object."""
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (target_width, target_height))
        except pygame.error as e:
            print(f"Error loading cloud image: {e}")
        self.speed = speed
        self.x = 0
        self.y = 0

    def update(self, delta: float) -> None:
        """Update the cloud's position."""
        self.x -= self.speed * delta
        if self.x <= -self.image.get_width():
            self.x = 0

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the cloud on the given surface."""
        surface.blit(self.image, (self.x, self.y))
        surface.blit(self.image, (self.x + self.image.get_width(), self.y))


class CloudManager:
    """Manages multiple cloud objects in the game."""

    def __init__(self, width: int, height: int) -> None:
        """Initialize the CloudManager."""
        self.width = width
        self.height = height
        self.clouds: list[Cloud] = []
        self._load_clouds()

    def _load_clouds(self) -> None:
        """Load cloud images and create Cloud objects."""
        cloud_groups = [group for group in os.listdir("assets/clouds") if Path("assets/clouds", group).is_dir()]
        cloud_group = random.choice(cloud_groups)
        cloud_path = f"assets/clouds/{cloud_group}"
        cloud_images = sorted(os.listdir(cloud_path))

        for i, image in enumerate(cloud_images):
            if not image.endswith(".png"):
                continue
            speed = 0 if i == 0 else 3 + i * 10
            cloud = Cloud(str(Path(cloud_path) / image), speed, self.width, self.height)
            self.clouds.append(cloud)

    def update(self, delta: float) -> None:
        """Update all clouds."""
        for cloud in self.clouds:
            cloud.update(delta)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all clouds on the given surface."""
        for cloud in self.clouds:
            cloud.draw(surface)

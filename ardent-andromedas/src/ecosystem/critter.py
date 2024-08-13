import io
import logging
from abc import ABC, abstractmethod

import pygame


class Critter(ABC):
    """Abstract base class representing a critter in the ecosystem simulation.

    This class defines the interface for critters, including their basic properties
    and required methods for updating, drawing, and lifecycle management.
    """

    def __init__(
        self, member_id: int, x: float, y: float, width: int, height: int, avatar: bytes | None = None
    ) -> None:
        """Initialize a new Critter instance.

        Args:
        ----
            member_id (int): Unique identifier for the critter.
            x (float): Initial x-coordinate of the critter.
            y (float): Initial y-coordinate of the critter.
            width (int): Width of the ecosystem area.
            height (int): Height of the ecosystem area.
            avatar (bytes | None): The avatar image data for the critter, if available.

        """
        self.member_id = member_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.alive = True

        self.avatar = avatar
        self.avatar_surface = None
        if self.avatar:
            try:
                avatar_io = io.BytesIO(self.avatar)
                avatar_image = pygame.image.load(avatar_io)
                self.avatar_surface = pygame.transform.scale(avatar_image, (64, 64)).convert_alpha()
            except pygame.error as e:
                print(f"Failed to create avatar surface for critter {member_id}: {e}")
            except Exception:
                logging.exception("Unexpected error creating avatar surface for snake %s", member_id)

    @abstractmethod
    def activate(self) -> None:
        """Activates the critter."""

    @abstractmethod
    def deactivate(self) -> None:
        """Deactivates the critter."""

    @abstractmethod
    def update(self, delta: float, activity: float) -> None:
        """Update the critter's state and position.

        Args:
        ----
            delta (float): Time elapsed since the last update.
            activity (float): Current activity level in the ecosystem.

        """

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the critter on the given surface.

        Args:
        ----
            surface (pygame.Surface): The surface to draw the critter on.

        """

    @abstractmethod
    def spawn(self) -> None:
        """Spawn the critter in the ecosystem."""

    @abstractmethod
    def despawn(self) -> None:
        """Despawn the critter from the ecosystem."""

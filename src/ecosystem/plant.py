import random

import pygame


class Plant:
    """Represents a plant in the ecosystem.

    Attributes
    ----------
        x (int): X-coordinate of the plant.
        y (int): Y-coordinate of the plant.
        size (float): Current size of the plant.
        max_size (int): Maximum size the plant can grow to.
        growth_rate (float): Rate at which the plant grows.
        color (tuple): RGB color of the plant.
        alive (bool): Whether the plant is alive or not.

    """

    def __init__(self, x: int, y: int) -> None:
        """Initialize a new Plant instance.

        Args:
        ----
            x (int): X-coordinate of the plant.
            y (int): Y-coordinate of the plant.

        """
        self.x = x
        self.y = y
        self.size = 0
        self.max_size = random.randint(20, 50)
        self.growth_rate = random.uniform(5, 15)
        self.color = (0, random.randint(100, 200), 0)
        self.alive = True

    def update(self, dt: float, activity: float) -> None:
        """Update the plant's state.

        Args:
        ----
            dt (float): Time delta since last update.
            activity (float): Environmental activity factor affecting growth.

        """
        if self.size < self.max_size:
            self.size += self.growth_rate * activity * dt
        elif random.random() < (1 - activity) * 0.5 * dt:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the plant on the given surface.

        Args:
        ----
            surface (pygame.Surface): Surface to draw the plant on.

        """
        pygame.draw.circle(surface, self.color, (self.x, self.y), int(self.size))

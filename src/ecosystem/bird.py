import math
import random

import pygame
from pygame import Surface, Vector2

from ecosystem.critter import Critter


class Bird(Critter):
    """Represents a bird in the ecosystem simulation.

    This class handles the bird's movement, appearance, and lifecycle.
    """

    def __init__(self, member_id: int, x: int, y: int, width: int, height: int) -> None:
        """Initialize a new Bird instance.

        Args:
        ----
            member_id (int): The unique identifier for the bird.
            x (int): The x-coordinate of the bird's position.
            y (int): The y-coordinate of the bird's position.
            width (int): The width of the simulation area.
            height (int): The height of the simulation area.

        """
        self.max_height = height * 0.6
        super().__init__(member_id, random.randint(0, width), random.randint(0, int(self.max_height)), width, height)
        self.position = Vector2(self.x, self.y)
        self.velocity = Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 2
        self.size = random.uniform(15, 25)
        self.color = self.generate_color()
        self.wing_angle = 0
        self.wing_speed = random.uniform(10, 15)
        self.turn_chance = 0.02
        self.target_angle = 0
        self.turn_speed = random.uniform(0.5, 1.5)

    def generate_color(self) -> tuple[int, int, int]:
        """Generate a random color for the bird.

        Returns
        -------
            tuple[int, int, int]: A tuple representing an RGB color.

        """
        return (
            random.randint(200, 255),
            random.randint(100, 200),
            random.randint(100, 200),
        )

    def activate(self) -> None:
        self.alive = True

    def deactivate(self) -> None:
        self.alive = False

    def update(self, delta: float, activity: float) -> None:
        """Update the bird's position and state.

        Args:
        ----
            delta (float): The time elapsed since the last update.
            activity (float): The current activity level of the simulation.

        """
        self.position += self.velocity * activity * delta * 60

        if self.position.x < 0 or self.position.x > self.width:
            self.velocity.x *= -1
        if self.position.y < 0 or self.position.y > self.max_height:
            self.velocity.y *= -1

        self.position.x = max(0, min(self.position.x, self.width))
        self.position.y = max(0, min(self.position.y, self.max_height))

        if random.random() < self.turn_chance:
            self.target_angle = random.uniform(-math.pi / 4, math.pi / 4)

        if abs(self.target_angle) > 0.01:
            turn_amount = self.turn_speed * delta
            turn_direction = 1 if self.target_angle > 0 else -1
            actual_turn = min(abs(self.target_angle), turn_amount) * turn_direction

            self.velocity.rotate_ip(math.degrees(actual_turn))
            self.target_angle -= actual_turn

        self.wing_angle = math.sin(pygame.time.get_ticks() * self.wing_speed * 0.001) * 45

        if random.random() < 0.001 * delta:
            self.alive = False

        self.x, self.y = self.position.x, self.position.y

    def draw(self, surface: Surface) -> None:
        """Draw the bird on the given surface.

        Args:
        ----
            surface (Surface): The pygame surface to draw on.

        """
        pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), int(self.size))

        left_wing = self.position + Vector2(-self.size, 0).rotate(self.wing_angle)
        right_wing = self.position + Vector2(self.size, 0).rotate(-self.wing_angle)
        pygame.draw.polygon(surface, self.color, [self.position, left_wing, right_wing])

        eye_position = self.position + self.velocity.normalize() * self.size * 0.5
        pygame.draw.circle(surface, (255, 255, 255), (int(eye_position.x), int(eye_position.y)), int(self.size * 0.2))
        pygame.draw.circle(surface, (0, 0, 0), (int(eye_position.x), int(eye_position.y)), int(self.size * 0.1))

        beak_position = self.position + self.velocity.normalize() * self.size
        pygame.draw.polygon(
            surface,
            (255, 200, 0),
            [
                beak_position,
                beak_position
                + Vector2(self.size * 0.3, self.size * 0.1).rotate(self.velocity.angle_to(Vector2(1, 0))),
                beak_position
                + Vector2(self.size * 0.3, -self.size * 0.1).rotate(self.velocity.angle_to(Vector2(1, 0))),
            ],
        )

    def spawn(self) -> None:
        """Respawn the bird at a random position in the top portion of the simulation area."""
        self.alive = True
        self.position = Vector2(random.randint(0, self.width), random.randint(0, int(self.max_height)))
        self.x, self.y = self.position.x, self.position.y

    def despawn(self) -> None:
        self.alive = False

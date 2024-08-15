import math
import random

import pygame
from pygame import Color, Surface, Vector2

from ecosystem.critter import Critter


class Snake(Critter):
    """Represents a snake in the ecosystem.

    The snake moves towards a target, grows in length, and can spawn or despawn.
    """

    def __init__(self, member_id: int, x: int, y: int, width: int, height: int, avatar: bytes | None = None) -> None:
        """Initialize a new Snake instance.

        Args:
        ----
            member_id (int): The unique identifier for the snake.
            x (int): Initial x-coordinate of the snake's head.
            y (int): Initial y-coordinate of the snake's head.
            width (int): Width of the game area.
            height (int): Height of the game area.
            avatar (bytes): The avatar data for the snake.

        """
        super().__init__(member_id, x, y, width, height, avatar)
        self.segments = [Vector2(x, y)]
        self.x = x
        self.y = y
        self.direction = Vector2(1, 0)
        self.min_y = int(self.height * 0.65)
        self.max_y = int(self.height * 0.80)
        self.speed = 2
        self.length = 50
        self.color = self.generate_color()
        self.target = self.get_new_target()
        self.state = "inactive"
        self.scale = 0.1

    def generate_color(self) -> Color:
        """Generate a random color for the snake.

        Returns
        -------
            Color: A pygame Color object with random RGB values.

        """
        return pygame.Color(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

    def get_new_target(self) -> Vector2:
        """Generate a new random target position for the snake.

        Returns
        -------
            Vector2: A new target position within the game area.

        """
        return Vector2(random.randint(0, self.width), random.randint(self.min_y, self.max_y))

    def update(self, delta: float, activity: float) -> None:
        """Update the snake's position and state.

        Args:
        ----
            delta (float): Time elapsed since the last update.
            activity (float): Activity level affecting the snake's speed.

        """
        if self.state == "inactive":
            return

        if self.state == "spawn":
            self.scale = min(1.0, self.scale + delta)
            if self.scale == 1.0:
                self.state = "active"
        elif self.state == "despawn":
            self.scale = max(0.0, self.scale - delta)
            if self.scale == 0.0:
                self.alive = False
                self.state = "inactive"
                return

        head = self.segments[0]
        to_target = self.target - head
        if to_target.length() < 10:
            self.target = self.get_new_target()

        to_target = self.target - head
        self.direction = to_target.normalize()
        new_head = head + self.direction * self.speed * activity * delta * 60

        new_head.y = max(min(new_head.y, self.max_y), self.min_y)
        new_head.x = new_head.x % self.width  # Wrap around horizontally

        self.segments.insert(0, new_head)
        if len(self.segments) > self.length:
            self.segments.pop()

        # Update self.x and self.y to match the new head position
        self.x = int(new_head.x)
        self.y = int(new_head.y)

    def draw(self, surface: Surface) -> None:
        """Draw the snake on the given surface.

        Args:
        ----
            surface (Surface): The pygame Surface to draw on.

        """
        # Draw body segments with sinusoidal wave
        time = pygame.time.get_ticks() / 1000
        for i, segment in enumerate(self.segments[1:], 1):
            radius = int((10 * (1 - i / len(self.segments)) + 5) * self.scale)
            alpha = int(255 * (1 - i / len(self.segments)))
            color = (*self.color[:3], alpha)

            # Apply sinusoidal wave
            wave_amplitude = 5 * self.scale * (1 - i / len(self.segments))
            wave_frequency = 0.2
            wave_speed = 3
            wave_offset = math.sin(time * wave_speed + i * wave_frequency) * wave_amplitude

            wave_vector = self.direction.rotate(90).normalize() * wave_offset
            wave_pos = segment + wave_vector

            pygame.draw.circle(surface, color, (int(wave_pos.x), int(wave_pos.y)), radius)

        # Draw head
        head = self.segments[0]
        head_radius = int(15 * self.scale)

        # Create a surface for the head
        head_surface = pygame.Surface((head_radius * 2, head_radius * 2), pygame.SRCALPHA)

        # Draw the base color of the head
        pygame.draw.circle(head_surface, self.color, (head_radius, head_radius), head_radius)

        # Apply avatar if available
        if self.avatar_surface:
            avatar_scaled = pygame.transform.scale(self.avatar_surface, (head_radius * 2, head_radius * 2))

            # Create a circular mask
            mask_surface = pygame.Surface((head_radius * 2, head_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(mask_surface, (255, 255, 255), (head_radius, head_radius), head_radius)

            # Apply mask to avatar
            avatar_scaled.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Blend avatar with head color
            head_surface.blit(avatar_scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Draw the head on the main surface
        surface.blit(head_surface, (int(head.x - head_radius), int(head.y - head_radius)))

        # Draw cuter eyes
        eye_offset = Vector2(7 * self.scale, 0)
        left_eye = head + eye_offset.rotate(0)
        right_eye = head + eye_offset.rotate(180)

        eye_radius = int(5 * self.scale)
        pupil_radius = int(3 * self.scale)

        # Draw eye whites
        pygame.draw.circle(surface, (255, 255, 255), (int(left_eye.x), int(left_eye.y)), eye_radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(right_eye.x), int(right_eye.y)), eye_radius)

        # Draw pupils with a slight upward offset
        pupil_offset = Vector2(0, -1 * self.scale)
        pygame.draw.circle(
            surface, (0, 0, 0), (int(left_eye.x + pupil_offset.x), int(left_eye.y + pupil_offset.y)), pupil_radius
        )
        pygame.draw.circle(
            surface, (0, 0, 0), (int(right_eye.x + pupil_offset.x), int(right_eye.y + pupil_offset.y)), pupil_radius
        )

    def activate(self) -> None:
        self.state = "spawn"
        self.scale = 0.1

    def deactivate(self) -> None:
        self.state = "despawn"

    def spawn(self) -> None:
        self.alive = True
        self.activate()
        self.segments = [Vector2(random.randint(0, self.width), random.randint(self.min_y, self.max_y))]
        self.x = int(self.segments[0].x)
        self.y = int(self.segments[0].y)
        self.color = self.generate_color()

    def despawn(self) -> None:
        self.deactivate()

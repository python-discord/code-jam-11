from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .critter import Critter


class SpeechBubble:
    """A class representing a speech bubble for a critter."""

    def __init__(
        self,
        critter: Critter,
        content: str,
        duration: float = 5.0,
        bg_color: tuple[int, int, int] = (255, 255, 255),
        text_color: tuple[int, int, int] = (0, 0, 0),
        border_color: tuple[int, int, int] = (0, 0, 0),
        font_size: int = 28,
        padding: int = 20,
        border_radius: int = 20,
        max_width: int = 400,
    ) -> None:
        """Initialize the SpeechBubble."""
        self.critter = critter
        self.content = content
        self.duration = duration
        self.creation_time = time.time()
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color
        self.font_size = font_size
        self.padding = padding
        self.border_radius = border_radius
        self.max_width = max_width
        self.opacity = 51

        self.font = pygame.font.Font(None, font_size)
        self.surface = None
        self.position = (self.critter.x, self.critter.y)
        self._create_surface()

    def _create_surface(self) -> None:
        words = self.content.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join([*current_line, word])
            if self.font.size(test_line)[0] <= self.max_width - 2 * self.padding:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        text_surfaces = [self.font.render(line, True, self.text_color) for line in lines]
        max_width = max(surface.get_width() for surface in text_surfaces)
        total_height = sum(surface.get_height() for surface in text_surfaces)

        self.surface = pygame.Surface(
            (max_width + 2 * self.padding, total_height + 2 * self.padding + 20), pygame.SRCALPHA
        )

        background = pygame.Surface((max_width + 2 * self.padding, total_height + 2 * self.padding), pygame.SRCALPHA)
        background.fill((*self.bg_color, self.opacity))
        self.surface.blit(background, (0, 0))

        pygame.draw.rect(
            self.surface,
            self.border_color,
            (0, 0, max_width + 2 * self.padding, total_height + 2 * self.padding),
            width=2,
            border_radius=self.border_radius,
        )

        y_offset = self.padding
        for surface in text_surfaces:
            self.surface.blit(surface, (self.padding, y_offset))
            y_offset += surface.get_height()

        self.tail_offset = 0

        self._draw_tail()

    def _draw_tail(self) -> None:
        tail_points = [
            (
                self.surface.get_width() // 2 + self.tail_offset - 40 // 2,
                self.surface.get_height() - 20,
            ),
            (self.surface.get_width() // 2 + self.tail_offset, self.surface.get_height()),
            (
                self.surface.get_width() // 2 + self.tail_offset + 40 // 2,
                self.surface.get_height() - 20,
            ),
        ]

        pygame.draw.rect(
            self.surface,
            (*self.bg_color, self.opacity),
            (0, self.surface.get_height() - 20 - 2, self.surface.get_width(), 20 + 2),
        )

        pygame.draw.polygon(self.surface, (*self.bg_color, self.opacity), tail_points)

        pygame.draw.rect(
            self.surface, self.border_color, self.surface.get_rect(), width=2, border_radius=self.border_radius
        )

        pygame.draw.lines(self.surface, self.border_color, False, tail_points, width=2)

    def update(self, delta: float) -> None:
        critter_x, critter_y = self.critter.x, self.critter.y
        bubble_width, bubble_height = self.surface.get_size()
        screen_width, screen_height = pygame.display.get_surface().get_size()

        x = critter_x - bubble_width // 2
        y = critter_y - bubble_height - 20

        x = max(0, min(x, screen_width - bubble_width))
        y = max(0, min(y, screen_height - bubble_height))

        self.position = (x, y)

        self.tail_offset = int(critter_x - (x + bubble_width // 2))
        self.tail_offset = max(-bubble_width // 2 + 20, min(self.tail_offset, bubble_width // 2 - 20))

        self._draw_tail()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.surface, self.position)

    def is_expired(self) -> bool:
        return time.time() - self.creation_time > self.duration

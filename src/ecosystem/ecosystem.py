import math

import pygame
import random
from .plant import Plant


class Ecosystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # 0 to 1, where 0 is barren and 1 is lush
        self.activity = 0
        self.time = 0
        self.surface = pygame.Surface((width, height))

        self.sky_colors = [
            # Barren gray
            (200, 200, 200),
            # Lush blue
            (135, 206, 235)
        ]
        self.ground_colors = [
            # Barren tan
            (210, 180, 140),
            # Lush green
            (34, 139, 34)
        ]

        self.plants = []

    def update(self, delta):
        self.time += delta
        self.activity = min(1, max(0, self.activity + math.sin(self.time / 4) * delta))

        for plant in self.plants:
            plant.update(delta, self.activity)

        if random.random() < self.activity * delta:
            self.plants.append(Plant(random.randint(0, self.width), self.height))

        self.plants = [plant for plant in self.plants if plant.alive]

    def draw(self):
        sky_color = self.interpolate_color(self.sky_colors[0], self.sky_colors[1], self.activity)
        self.surface.fill(sky_color)

        ground_color = self.interpolate_color(self.ground_colors[0], self.ground_colors[1], self.activity)
        pygame.draw.rect(self.surface, ground_color, (0, self.height * 0.7, self.width, self.height * 0.3))

        for plant in self.plants:
            plant.draw(self.surface)

        return self.surface

    @staticmethod
    def interpolate_color(color1, color2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(color1, color2))


def run_pygame():
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Discord Ecosystem Visualization")
    clock = pygame.time.Clock()

    ecosystem = Ecosystem(width, height)

    running = True
    while running:
        delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ecosystem.update(delta)
        screen.blit(ecosystem.draw(), (0, 0))
        pygame.display.flip()

    pygame.quit()

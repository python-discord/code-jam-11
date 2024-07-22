import random

import pygame


class Plant:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.size = 0
        self.max_size = random.randint(20, 50)
        self.growth_rate = random.uniform(5, 15)
        self.color = (0, random.randint(100, 200), 0)
        self.alive = True

    def update(self, dt: float, activity: float) -> None:
        if self.size < self.max_size:
            self.size += self.growth_rate * activity * dt
        elif random.random() < (1 - activity) * 0.5 * dt:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color, (self.x, self.y), int(self.size))

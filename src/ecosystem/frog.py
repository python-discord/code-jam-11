import math
import random

import pygame


class Frog:
    def __init__(self, x: float, y: float, width: int, height: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.size = random.uniform(20, 30)
        self.color = (random.randint(50, 100), random.randint(150, 200), random.randint(50, 100))
        self.eye_color = (255, 255, 255)
        self.pupil_color = (0, 0, 0)

        self.jump_height = random.uniform(50, 100)
        self.jump_duration = random.uniform(0.5, 1.0)
        self.rest_duration = random.uniform(1.0, 3.0)

        self.state = "rest"
        self.state_time = 0
        self.jump_start_y = self.y
        self.jump_target_x = self.x

        self.scale = 1.0
        self.alive = True

    def update(self, delta: float, activity: float) -> None:
        self.state_time += delta

        if self.state == "rest":
            if self.state_time >= self.rest_duration:
                self.start_jump()
        elif self.state == "jump":
            progress = self.state_time / self.jump_duration
            if progress <= 1:
                self.y = self.jump_start_y - self.jump_height * math.sin(progress * math.pi)
                self.x += (self.jump_target_x - self.x) * delta / self.jump_duration
            else:
                self.state = "rest"
                self.state_time = 0
                self.y = self.jump_start_y

        if random.random() < 0.01 * delta:
            self.alive = False

    def start_jump(self) -> None:
        self.state = "jump"
        self.state_time = 0
        self.jump_start_y = self.y
        jump_distance = random.uniform(50, 150)
        self.jump_target_x = max(0, min(self.width, self.x + random.uniform(-jump_distance, jump_distance)))

    def draw(self, surface: pygame.Surface) -> None:
        self.scale = 0.5 + (self.y / self.height) * 0.5

        scaled_size = int(self.size * self.scale)
        body_rect = pygame.Rect(self.x - scaled_size // 2, self.y - scaled_size // 2, scaled_size, scaled_size)
        pygame.draw.ellipse(surface, self.color, body_rect)

        eye_size = scaled_size // 4
        left_eye_pos = (int(self.x - scaled_size // 4), int(self.y - scaled_size // 4))
        right_eye_pos = (int(self.x + scaled_size // 4), int(self.y - scaled_size // 4))

        pygame.draw.circle(surface, self.eye_color, left_eye_pos, eye_size)
        pygame.draw.circle(surface, self.eye_color, right_eye_pos, eye_size)

        pupil_size = eye_size // 2
        pygame.draw.circle(surface, self.pupil_color, left_eye_pos, pupil_size)
        pygame.draw.circle(surface, self.pupil_color, right_eye_pos, pupil_size)

        mouth_rect = pygame.Rect(self.x - scaled_size // 4, self.y, scaled_size // 2, scaled_size // 4)
        pygame.draw.arc(surface, (50, 50, 50), mouth_rect, math.pi, 2 * math.pi, 2)

    def spawn(self) -> None:
        self.alive = True
        self.y = self.height
        self.x = random.randint(0, self.width)
        self.scale = 0.1

    def despawn(self) -> None:
        self.alive = False

import random
import pygame
from pygame import Vector2


class Snake:
    def __init__(self, x, y, width, height):
        self.width = width
        self.height = height
        self.segments = [Vector2(x, y)]
        self.direction = Vector2(1, 0)
        self.speed = 2
        self.length = 50
        self.color = self.generate_color()
        self.target = self.get_new_target()
        self.alive = True
        self.state = "spawn"
        self.scale = 0.1

    def generate_color(self):
        return pygame.Color(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

    def get_new_target(self):
        return Vector2(random.randint(0, self.width), random.randint(int(self.height * 0.7), self.height))

    def update(self, delta, activity):
        if self.state == "spawn":
            self.scale = min(1.0, self.scale + delta)
            if self.scale == 1.0:
                self.state = "normal"
        elif self.state == "despawn":
            self.scale = max(0.0, self.scale - delta)
            if self.scale == 0.0:
                self.alive = False
                return

        head = self.segments[0]
        to_target = self.target - head
        if to_target.length() < 10:
            self.target = self.get_new_target()

        to_target = self.target - head
        self.direction = to_target.normalize()
        new_head = head + self.direction * self.speed * activity * delta * 60

        self.segments.insert(0, new_head)
        if len(self.segments) > self.length:
            self.segments.pop()

    def draw(self, surface):
        for i, segment in enumerate(self.segments):
            radius = int((10 * (1 - i / len(self.segments)) + 5) * self.scale)
            alpha = int(255 * (1 - i / len(self.segments)))
            color = (self.color.r, self.color.g, self.color.b, alpha)
            pygame.draw.circle(surface, color, (int(segment.x), int(segment.y)), radius)

        head = self.segments[0]
        eye_offset = self.direction.normalize() * 8 * self.scale
        left_eye = head + eye_offset.rotate(90)
        right_eye = head + eye_offset.rotate(-90)

        eye_radius = int(4 * self.scale)
        pupil_radius = int(2 * self.scale)
        pygame.draw.circle(surface, (255, 255, 255), (int(left_eye.x), int(left_eye.y)), eye_radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(right_eye.x), int(right_eye.y)), eye_radius)
        pygame.draw.circle(surface, (0, 0, 0), (int(left_eye.x), int(left_eye.y)), pupil_radius)
        pygame.draw.circle(surface, (0, 0, 0), (int(right_eye.x), int(right_eye.y)), pupil_radius)

    def spawn(self):
        self.alive = True
        self.scale = 0.1
        self.state = "spawn"
        self.segments = [Vector2(random.randint(0, self.width), self.height)]
        self.color = self.generate_color()

    def start_despawn(self):
        self.state = "despawn"

import contextlib

# Hide pygame welcome message
with contextlib.redirect_stdout(None):
    import pygame

import random
import os
import time
from collections import deque
from queue import Queue
from PIL import Image
from .plant import Plant
from .frog import Frog
from .snake import Snake
from .bird import Bird


class Ecosystem:
    def __init__(self, width, height, generate_gifs=False, gif_interval=5, gif_duration=5, fps=30):
        self.width = width
        self.height = height
        self.activity = 1
        self.elapsed_time = 0
        self.surface = pygame.Surface((width, height))

        self.sky_colors = [
            (200, 200, 200),  # Barren gray
            (135, 206, 235)  # Lush blue
        ]
        self.ground_colors = [
            (210, 180, 140),  # Barren tan
            (34, 139, 34)  # Lush green
        ]

        self.plants = []
        self.frogs = []
        self.snakes = []
        self.birds = []

        self.font = pygame.font.Font(None, 24)
        self.setup_ui()

        # GIF generation attributes
        self.generate_gifs = generate_gifs
        self.gif_interval = gif_interval
        self.gif_duration = gif_duration
        self.fps = fps
        if generate_gifs:
            self.frame_queue = deque(maxlen=fps * gif_duration)
            self.gif_queue = Queue()
            self.gif_dir = "ecosystem_gifs"
            os.makedirs(self.gif_dir, exist_ok=True)
            self.last_gif_time = 0

    def setup_ui(self):
        button_width = 120
        button_height = 30
        button_spacing = 10
        top_margin = 20
        left_margin = 20

        self.activity_slider = pygame.Rect(left_margin, top_margin, 200, 20)

        button_y = top_margin + self.activity_slider.height + button_spacing

        self.spawn_plant_button = Button(left_margin, button_y, button_width, button_height, "Spawn Plant", (0, 255, 0),
                                         (0, 0, 0), self.font)

        self.spawn_frog_button = Button(left_margin + button_width + button_spacing, button_y, button_width,
                                        button_height, "Spawn Frog", (0, 0, 255), (255, 255, 255), self.font)

        self.spawn_snake_button = Button(left_margin + (button_width + button_spacing) * 2, button_y, button_width,
                                         button_height, "Spawn Snake", (255, 200, 0), (0, 0, 0), self.font)

        self.spawn_bird_button = Button(left_margin + (button_width + button_spacing) * 3, button_y, button_width,
                                        button_height, "Spawn Bird", (100, 100, 255), (255, 255, 255), self.font)

        self.reset_button = Button(left_margin + (button_width + button_spacing) * 4, button_y, button_width,
                                   button_height, "Reset", (255, 0, 0), (255, 255, 255), self.font)

    def update(self, delta):
        self.elapsed_time += delta

        for plant in self.plants:
            plant.update(delta, self.activity)

        for frog in self.frogs:
            frog.update(delta, self.activity)

        for snake in self.snakes:
            snake.update(delta, self.activity)

        for bird in self.birds:
            bird.update(delta, self.activity)

        if random.random() < self.activity * delta:
            self.spawn_plant()

        if random.random() < self.activity * delta * 0.5:
            self.spawn_frog()

        if random.random() < self.activity * delta * 0.3:
            self.spawn_snake()

        if random.random() < self.activity * delta * 0.4:
            self.spawn_bird()

        self.plants = [plant for plant in self.plants if plant.alive]
        self.frogs = [frog for frog in self.frogs if frog.alive]
        self.snakes = [snake for snake in self.snakes if snake.alive]
        self.birds = [bird for bird in self.birds if bird.alive]

        if self.generate_gifs:
            self.frame_queue.append(pygame.image.tostring(self.surface, 'RGB'))
            current_time = time.time()
            if current_time - self.last_gif_time >= self.gif_interval:
                self._generate_gif()
                self.last_gif_time = current_time

    def draw(self):
        sky_color = self.interpolate_color(self.sky_colors[0], self.sky_colors[1], self.activity)
        self.surface.fill(sky_color)

        ground_color = self.interpolate_color(self.ground_colors[0], self.ground_colors[1], self.activity)
        pygame.draw.rect(self.surface, ground_color, (0, self.height * 0.7, self.width, self.height * 0.3))

        for plant in self.plants:
            plant.draw(self.surface)

        for frog in self.frogs:
            frog.draw(self.surface)

        for snake in self.snakes:
            snake.draw(self.surface)

        for bird in self.birds:
            bird.draw(self.surface)

        return self.surface

    def reset(self):
        self.activity = 0.5
        self.elapsed_time = 0
        self.plants = []
        self.frogs = []
        self.snakes = []
        self.birds = []

    def spawn_plant(self):
        self.plants.append(Plant(random.randint(0, self.width), self.height * 0.7))

    def spawn_frog(self):
        new_frog = Frog(random.randint(0, self.width), self.height - 20, self.width, self.height)
        new_frog.spawn()
        self.frogs.append(new_frog)

    def spawn_snake(self):
        new_snake = Snake(random.randint(0, self.width), self.height * 0.7, self.width, self.height)
        new_snake.spawn()
        self.snakes.append(new_snake)

    def spawn_bird(self):
        new_bird = Bird(self.width, self.height)
        new_bird.spawn()
        self.birds.append(new_bird)

    @staticmethod
    def interpolate_color(color1, color2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(color1, color2))

    def _generate_gif(self):
        gif_path = os.path.join(self.gif_dir, f"ecosystem_{time.time()}.gif")
        frames = [Image.frombytes('RGB', (self.width, self.height), frame) for frame in self.frame_queue]

        frames[0].save(gif_path, save_all=True, append_images=frames[1:], optimize=False, duration=1000 // self.fps,
                       loop=0)
        self.gif_queue.put((gif_path, time.time()))

    def get_latest_gif(self):
        if self.gif_queue.empty():
            return None
        return self.gif_queue.get()


class Button:
    def __init__(self, x, y, width, height, text, color, text_color, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = font

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


def run_pygame(show_controls=True, generate_gifs=False):
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Ecosystem Visualization")
    clock = pygame.time.Clock()

    ecosystem = Ecosystem(width, height, generate_gifs=generate_gifs)

    running = True
    while running:
        delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif show_controls and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    position = pygame.mouse.get_pos()
                    if ecosystem.activity_slider.collidepoint(position):
                        ecosystem.activity = (position[
                                                  0] - ecosystem.activity_slider.x) / ecosystem.activity_slider.width
                    elif ecosystem.spawn_plant_button.is_clicked(position):
                        ecosystem.spawn_plant()
                    elif ecosystem.spawn_frog_button.is_clicked(position):
                        ecosystem.spawn_frog()
                    elif ecosystem.spawn_snake_button.is_clicked(position):
                        ecosystem.spawn_snake()
                    elif ecosystem.spawn_bird_button.is_clicked(position):
                        ecosystem.spawn_bird()
                    elif ecosystem.reset_button.is_clicked(position):
                        ecosystem.reset()

        ecosystem.update(delta)
        screen.blit(ecosystem.draw(), (0, 0))

        if show_controls:
            pygame.draw.rect(screen, (200, 200, 200), ecosystem.activity_slider)
            pygame.draw.rect(screen, (0, 255, 0), (
                ecosystem.activity_slider.x, ecosystem.activity_slider.y,
                ecosystem.activity_slider.width * ecosystem.activity,
                ecosystem.activity_slider.height))

            ecosystem.spawn_plant_button.draw(screen)
            ecosystem.spawn_frog_button.draw(screen)
            ecosystem.spawn_snake_button.draw(screen)
            ecosystem.spawn_bird_button.draw(screen)
            ecosystem.reset_button.draw(screen)

            activity_text = ecosystem.font.render(f"Activity: {ecosystem.activity:.2f}", True, (0, 0, 0))
            screen.blit(activity_text, (20, 90))

            plants_text = ecosystem.font.render(f"Plants: {len(ecosystem.plants)}", True, (0, 0, 0))
            screen.blit(plants_text, (20, 110))

            frogs_text = ecosystem.font.render(f"Frogs: {len(ecosystem.frogs)}", True, (0, 0, 0))
            screen.blit(frogs_text, (20, 130))

            snakes_text = ecosystem.font.render(f"Snakes: {len(ecosystem.snakes)}", True, (0, 0, 0))
            screen.blit(snakes_text, (20, 150))

            birds_text = ecosystem.font.render(f"Birds: {len(ecosystem.birds)}", True, (0, 0, 0))
            screen.blit(birds_text, (20, 170))

        pygame.display.flip()

        if generate_gifs:
            latest_gif = ecosystem.get_latest_gif()
            if latest_gif:
                gif_path, timestamp = latest_gif
                print(f"New GIF generated at {timestamp}: {gif_path}")

    pygame.quit()


def run_gif_generator(duration=None):
    pygame.init()
    width, height = 800, 600
    ecosystem = Ecosystem(width, height, generate_gifs=True)
    clock = pygame.time.Clock()

    start_time = time.time()
    running = True
    while running:
        delta = clock.tick(60) / 1000.0
        ecosystem.update(delta)
        ecosystem.draw()

        if duration and time.time() - start_time > duration:
            running = False

        latest_gif = ecosystem.get_latest_gif()
        if latest_gif:
            yield latest_gif

    pygame.quit()

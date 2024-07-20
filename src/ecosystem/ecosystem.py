import pygame
import random
from .plant import Plant
from .frog import Frog
from .snake import Snake


class Ecosystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.activity = 0.5  # Start with medium activity
        self.time = 0
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

    def update(self, delta):
        self.time += delta

        for plant in self.plants:
            plant.update(delta, self.activity)

        for frog in self.frogs:
            frog.update(delta, self.activity)

        for snake in self.snakes:
            snake.update(delta, self.activity)

        if random.random() < self.activity * delta:
            self.plants.append(Plant(random.randint(0, self.width), self.height))

        if random.random() < self.activity * delta * 0.5:
            new_frog = Frog(random.randint(0, self.width), self.height - 20, self.width, self.height)
            new_frog.spawn()
            self.frogs.append(new_frog)

        if random.random() < self.activity * delta * 0.3:
            self.spawn_snake()

        self.plants = [plant for plant in self.plants if plant.alive]
        self.frogs = [frog for frog in self.frogs if frog.alive]
        self.snakes = [snake for snake in self.snakes if snake.alive]

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

        return self.surface

    def reset(self):
        self.activity = 0.5
        self.time = 0
        self.plants = []
        self.frogs = []
        self.snakes = []

    def spawn_plant(self):
        self.plants.append(Plant(random.randint(0, self.width), self.height))

    def spawn_frog(self):
        new_frog = Frog(random.randint(0, self.width), self.height - 20, self.width, self.height)
        new_frog.spawn()
        self.frogs.append(new_frog)

    def spawn_snake(self):
        new_snake = Snake(random.randint(0, self.width), self.height, self.width, self.height)
        new_snake.spawn()
        self.snakes.append(new_snake)

    @staticmethod
    def interpolate_color(color1, color2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(color1, color2))


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


def run_pygame(show_controls=True):
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Discord Ecosystem Visualization")
    clock = pygame.time.Clock()

    ecosystem = Ecosystem(width, height)

    font = pygame.font.Font(None, 24)

    activity_slider = pygame.Rect(20, 20, 200, 20)
    spawn_plant_button = Button(20, 50, 120, 30, "Spawn Plant", (0, 255, 0), (0, 0, 0), font)
    spawn_frog_button = Button(150, 50, 120, 30, "Spawn Frog", (0, 0, 255), (255, 255, 255), font)
    spawn_snake_button = Button(280, 50, 120, 30, "Spawn Snake", (255, 200, 0), (0, 0, 0), font)
    reset_button = Button(410, 50, 100, 30, "Reset", (255, 0, 0), (255, 255, 255), font)

    running = True
    while running:
        delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif show_controls and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if activity_slider.collidepoint(pos):
                        ecosystem.activity = (pos[0] - activity_slider.x) / activity_slider.width
                    elif spawn_plant_button.is_clicked(pos):
                        ecosystem.spawn_plant()
                    elif spawn_frog_button.is_clicked(pos):
                        ecosystem.spawn_frog()
                    elif spawn_snake_button.is_clicked(pos):
                        ecosystem.spawn_snake()
                    elif reset_button.is_clicked(pos):
                        ecosystem.reset()

        ecosystem.update(delta)
        screen.blit(ecosystem.draw(), (0, 0))

        if show_controls:
            pygame.draw.rect(screen, (200, 200, 200), activity_slider)
            pygame.draw.rect(screen, (0, 255, 0), (
                activity_slider.x, activity_slider.y, activity_slider.width * ecosystem.activity,
                activity_slider.height))
            spawn_plant_button.draw(screen)
            spawn_frog_button.draw(screen)
            spawn_snake_button.draw(screen)
            reset_button.draw(screen)

            activity_text = font.render(f"Activity: {ecosystem.activity:.2f}", True, (0, 0, 0))
            screen.blit(activity_text, (20, 90))

            plants_text = font.render(f"Plants: {len(ecosystem.plants)}", True, (0, 0, 0))
            screen.blit(plants_text, (20, 110))

            frogs_text = font.render(f"Frogs: {len(ecosystem.frogs)}", True, (0, 0, 0))
            screen.blit(frogs_text, (20, 130))

            snakes_text = font.render(f"Snakes: {len(ecosystem.snakes)}", True, (0, 0, 0))
            screen.blit(snakes_text, (20, 150))

        pygame.display.flip()

    pygame.quit()

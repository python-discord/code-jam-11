import pygame
import random
from .plant import Plant
from .frog import Frog
from .snake import Snake
from .bird import Bird


class Ecosystem:
    def __init__(self, width, height):
        self.spawn_plant_button = None
        self.width = width
        self.height = height
        self.activity = 0.5
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
        self.birds = []

        self.font = pygame.font.Font(None, 24)
        self.activity_slider = None
        self.spawn_frog_button = None
        self.spawn_snake_button = None
        self.spawn_bird_button = None
        self.reset_button = None
        self.setup_ui()

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

        for bird in self.birds:
            bird.update(delta, self.activity)

        if random.random() < self.activity * delta * 0.4:
            self.spawn_bird()

        self.plants = [plant for plant in self.plants if plant.alive]
        self.frogs = [frog for frog in self.frogs if frog.alive]
        self.snakes = [snake for snake in self.snakes if snake.alive]
        self.birds = [bird for bird in self.birds if bird.alive]

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
        self.time = 0
        self.plants = []
        self.frogs = []
        self.snakes = []
        self.birds = []

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

    def spawn_bird(self):
        new_bird = Bird(self.width, self.height)
        new_bird.spawn()
        self.birds.append(new_bird)

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
                        ecosystem.activity = (position[0] - ecosystem.activity_slider.x) / ecosystem.activity_slider.width
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

    pygame.quit()

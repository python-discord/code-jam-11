import pygame
from wordcloud import WordCloud


class WordCloudObject:
    """Represents a full-screen word cloud object in the game."""

    def __init__(self, words: str, width: int, height: int, speed: float) -> None:
        """Initialize the WordCloudObject."""
        self.words = words
        self.width = width
        self.height = height
        self.speed = speed
        self.image = None
        self.strength = 24

    def generate_wordcloud(self, surface: pygame.Surface, words: str) -> None:
        """Generate a new word cloud with white text."""
        self.wordcloud = WordCloud(
            width=self.width,
            height=self.height,
            background_color=None,
            mode="RGBA",
            color_func=lambda *_: (self.strength, self.strength, self.strength),
        ).generate(words)

        wordcloud_image = self.wordcloud.to_image()
        self.image = pygame.image.fromstring(wordcloud_image.tobytes(), wordcloud_image.size, wordcloud_image.mode)
        self.image = self.image.convert_alpha()

    def change_words(self, new_words: str) -> None:
        """Change the words in the word cloud."""
        self.words = new_words
        self.generate_wordcloud(self.surface, self.words)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the word cloud on the given surface using blend mode."""
        if self.image is None:
            self.generate_wordcloud(surface, self.words)

        # Blend the word cloud with the background
        surface.blit(self.image, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

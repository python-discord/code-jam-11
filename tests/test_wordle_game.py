import unittest
from collections.abc import Generator

from app.core.wordle import WordleGame


class TestWordleGame(unittest.TestCase):
    """Tests for Wordle Game."""

    def test_color_for_guess(self) -> None:
        """Tests that matching colors are correct."""
        guess = "zehfq"
        word = "hello"

        game = WordleGame()
        colors = game.gen_colors_for_guess(guess, word)
        assert isinstance(colors, Generator)
        assert list(colors) == [4, 0, 1, 3, 2]

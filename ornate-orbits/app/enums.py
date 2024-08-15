from enum import IntEnum


class MatchResult(IntEnum):
    """Meaningful guess result."""

    CORRECT_LETTER_CORRECT_POSITION = 0
    CORRECT_LETTER_WRONG_POSITION = 1
    DEVIATED_LETTER_CORRECT_POSITION = 2
    DEVIATED_LETTER_WRONG_POSITION = 3
    WRONG_LETTER = 4

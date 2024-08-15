from datetime import datetime
from enum import StrEnum, auto

from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TriviaDifficulty(StrEnum):
    """Enum for Trivia difficulties."""

    EASY = auto()
    MEDIUM = auto()
    HARD = auto()


class Trivia(Base):
    """Trivia model."""

    __tablename__ = "trivia"

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    difficulty: Mapped[TriviaDifficulty]
    category: Mapped[str]
    question: Mapped[str]
    correct_answer: Mapped[str]
    incorrect_answer_1: Mapped[str]
    incorrect_answer_2: Mapped[str]
    incorrect_answer_3: Mapped[str]

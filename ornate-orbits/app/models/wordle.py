from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import asc, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .guess import Guess


class WordleStatus(Enum):
    """Status of Wordle."""

    ACTIVE = 0
    COMPLETED = 1
    PENDING = 2
    ABORTED = 3


class Wordle(Base):
    """Wordle model."""

    __tablename__ = "wordle"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        index=True,
        default=uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    word: Mapped[str]
    user_id: Mapped[int]
    status: Mapped[int]

    guesses: Mapped[list["Guess"]] = relationship(
        back_populates="wordle",
        order_by=asc(text("Guess.created_at")),
        lazy="selectin",
    )

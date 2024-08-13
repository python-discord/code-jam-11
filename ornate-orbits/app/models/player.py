from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Player(Base):
    """Player model."""

    __tablename__ = "player"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)
    username: Mapped[str]
    display_name: Mapped[str]

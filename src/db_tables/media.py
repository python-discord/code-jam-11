"""This file houses all tvdb media related database tables.

Some of these tables only have one column (`tvdb_id`), which may seem like a mistake, but is intentional.
That's because this provides better type safety and allows us to define proper foreign key relationships that
refer to these tables instead of duplicating that data.
It also may become useful if at any point we would
want to store something extra that's global to each movie / show / episode.
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.database import Base


class Movie(Base):
    """Table to store movies."""

    __tablename__ = "movies"

    tvdb_id: Mapped[int] = mapped_column(primary_key=True)


class Series(Base):
    """Table to store series."""

    __tablename__ = "series"

    tvdb_id: Mapped[int] = mapped_column(primary_key=True)


class Episode(Base):
    """Table to store episodes of series."""

    __tablename__ = "episodes"

    tvdb_id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("series.tvdb_id"))

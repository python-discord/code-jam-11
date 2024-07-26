from enum import Enum
from typing import ClassVar, TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.database import Base

# Prevent circular imports for relationships
if TYPE_CHECKING:
    from src.db_tables.media import Episode, Movie, Series
    from src.db_tables.user import User


class UserListKind(Enum):
    """Enum to represent the kind of items that are stored in a user list."""

    SERIES = "series"
    MOVIE = "movie"
    EPISODE = "episode"
    MEDIA = "media"  # either series or movie
    ANY = "any"


class UserListItemKind(Enum):
    """Enum to represent the kind of item in a user list."""

    SERIES = 0
    MOVIE = 1
    EPISODE = 2


class UserList(Base):
    """Table to store user lists.

    This provides a dynamic way to store various lists of media for the user, such as favorites, to watch,
    already watched, ... all tracked in the same table, instead of having to define tables for each such
    structure.
    """

    __tablename__ = "user_lists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    item_kind: Mapped[UserListKind] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="lists")
    items: Mapped[list["UserListItem"]] = relationship("UserListItem", back_populates="user_list")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="unique_user_list_name"),
        Index(
            "ix_user_lists_user_id_name",
            "user_id",
            "name",
            unique=True,
        ),
    )


class UserListItem(Base):
    """Base class for items in a user list."""

    __tablename__ = "user_list_items"
    list_id: Mapped[int] = mapped_column(ForeignKey("user_lists.id"), primary_key=True)
    tvdb_id: Mapped[int] = mapped_column(primary_key=True)

    user_list: Mapped["UserList"] = relationship("UserList", back_populates="items")
    kind: Mapped[UserListItemKind] = mapped_column(nullable=False, primary_key=True)

    __mapper_args__: ClassVar = {"polymorphic_on": tvdb_id, "polymorphic_identity": "base"}


class UserListItemSeries(UserListItem):
    """Represents a reference to a series in a user list."""

    __mapper_args__: ClassVar = {
        "polymorphic_identity": "series",
    }

    tvdb_id: Mapped[int] = mapped_column(
        ForeignKey("series.tvdb_id"), nullable=False, use_existing_column=True, primary_key=True
    )
    series: Mapped["Series"] = relationship("Series")


class UserListItemMovie(UserListItem):
    """Represents a reference to a movie in a user list."""

    __mapper_args__: ClassVar = {
        "polymorphic_identity": "movie",
    }

    tvdb_id: Mapped[int] = mapped_column(
        ForeignKey("movies.tvdb_id"), nullable=False, use_existing_column=True, primary_key=True
    )
    movie: Mapped["Movie"] = relationship("Movie")


class UserListItemEpisode(UserListItem):
    """Represents a reference to an episode in a user list."""

    __mapper_args__: ClassVar = {
        "polymorphic_identity": "episode",
    }

    tvdb_id: Mapped[int] = mapped_column(
        ForeignKey("episodes.tvdb_id"), nullable=False, use_existing_column=True, primary_key=True
    )
    episode: Mapped["Episode"] = relationship("Episode")

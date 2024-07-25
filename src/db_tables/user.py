from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.database import Base

# Prevent circular imports for relationships
if TYPE_CHECKING:
    from src.db_tables.user_list import UserList


class User(Base):
    """Table to store users."""

    __tablename__ = "users"

    discord_id: Mapped[int] = mapped_column(primary_key=True)

    lists: Mapped[list["UserList"]] = relationship("UserList", back_populates="user")

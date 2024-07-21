<!-- vi: tw=119
-->

# Welcome to `db_tables` directory

This directory defines all of our database tables. To do so, we're using [`SQLAlchemy`](https://docs.sqlalchemy.org)
ORM. That means our database tables are defined as python classes, that follow certain special syntax to achieve this.

All of these tables must inherit from the `Base` class, that can be imported from `src.utils.database` module.

There is no need to register newly created classes / files anywhere, as all files in this directory (except those
starting with `_`) will be automatically imported and picked up by SQLAlchemy.

## Example database class

Imagine an application that schedules appointmnets for users:

`user.py`:

```python
import enum
from typing import TYPE_CHECKING
from sqlalchemy import Mapped, mapped_column, relationship

from src.utils.database import Base


# Prevent circular imports for relationships
if TYPE_CHECKING:
    from src.db_tables.appointment import Appointment


class Role(enum.IntEnum):
    """Enumeration of all possible user roles."""

    USER = 0
    ADMIN = 1


class User(Base):
    """User database table."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    surname: Mapped[str] = mapped_column(nullable=False)
    user_role: Mapped[Role] = mapped_column(nullable=False, default=Role.USER)

    appointments: Mapped[list["Appointment"]] = relationship(
        lazy="selectin",
        back_populates="user",
        cascade="all, delete-orphan",
    )
```

`appointment.py`:

```python
from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.database import Base

# Prevent circular imports for relationships
if TYPE_CHECKING:
    from src.db_tables.user import User


class Appointment(Base):
    """Appointment database table."""

    __tablename__ = "appointment"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, nullable=False)
    booked_date: Mapped[date] = mapped_column(nullable=False)
    booked_time: Mapped[time] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    user: Mapped["User"] = relationship(lazy="selectin", back_populates="appointments")
```

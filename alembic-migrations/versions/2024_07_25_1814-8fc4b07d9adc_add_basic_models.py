"""Add basic models

Revision ID: 8fc4b07d9adc
Revises: c55da3c62644
Create Date: 2024-07-25 18:14:19.322905
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8fc4b07d9adc"
down_revision: str | None = "c55da3c62644"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table("movies", sa.Column("tvdb_id", sa.Integer(), nullable=False), sa.PrimaryKeyConstraint("tvdb_id"))
    op.create_table("shows", sa.Column("tvdb_id", sa.Integer(), nullable=False), sa.PrimaryKeyConstraint("tvdb_id"))
    op.create_table(
        "users", sa.Column("discord_id", sa.Integer(), nullable=False), sa.PrimaryKeyConstraint("discord_id")
    )
    op.create_table(
        "episodes",
        sa.Column("tvdb_id", sa.Integer(), nullable=False),
        sa.Column("show_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["show_id"],
            ["shows.tvdb_id"],
        ),
        sa.PrimaryKeyConstraint("tvdb_id"),
    )
    op.create_table(
        "user_lists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("item_kind", sa.Enum("SHOW", "MOVIE", "EPISODE", "MEDIA", "ANY", name="itemkind"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.discord_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="unique_user_list_name"),
    )
    op.create_index("ix_user_lists_user_id_name", "user_lists", ["user_id", "name"], unique=True)
    op.create_table(
        "user_list_items",
        sa.Column("list_id", sa.Integer(), nullable=False),
        sa.Column("tvdb_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["list_id"],
            ["user_lists.id"],
        ),
        sa.PrimaryKeyConstraint("list_id", "tvdb_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_list_items")
    op.drop_index("ix_user_lists_user_id_name", table_name="user_lists")
    op.drop_table("user_lists")
    op.drop_table("episodes")
    op.drop_table("users")
    op.drop_table("shows")
    op.drop_table("movies")
    # ### end Alembic commands ###

"""Initial schema — players, aliases, sessions, servers

Revision ID: 001
Revises:
Create Date: 2026-03-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "servers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column(
            "type",
            sa.Enum("official", "private", name="servertype"),
            nullable=False,
        ),
        sa.Column("battlemetrics_id", sa.String(64), nullable=True, unique=True),
        sa.Column("rcon_host", sa.String(256), nullable=True),
        sa.Column("rcon_port", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
    )

    op.create_table(
        "players",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("eos_id", sa.String(128), nullable=False, unique=True),
        sa.Column("steam_id", sa.String(64), nullable=True),
        sa.Column(
            "first_seen",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("total_sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_players_eos_id", "players", ["eos_id"], unique=True)
    op.create_index("ix_players_steam_id", "players", ["steam_id"])

    op.create_table(
        "aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column(
            "first_seen",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_aliases_name", "aliases", ["name"])

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column(
            "server_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("servers.id"),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("name_used", sa.String(128), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_index("ix_aliases_name", table_name="aliases")
    op.drop_table("aliases")
    op.drop_index("ix_players_steam_id", table_name="players")
    op.drop_index("ix_players_eos_id", table_name="players")
    op.drop_table("players")
    op.drop_table("servers")
    op.execute("DROP TYPE IF EXISTS servertype")

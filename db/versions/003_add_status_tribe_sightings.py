"""Add status and tribe to players, add sightings table

Revision ID: 003
Revises: 002
Create Date: 2026-04-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("players", sa.Column("status", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("players", sa.Column("tribe", sa.String(128), nullable=True))
    op.create_index("ix_players_tribe", "players", ["tribe"])

    op.create_table(
        "sightings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("server_name", sa.String(256), nullable=False),
        sa.Column("seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reported_by_discord_id", sa.String(64), nullable=False),
        sa.Column("reported_by_name", sa.String(128), nullable=False),
    )
    op.create_index("ix_sightings_server_name", "sightings", ["server_name"])
    op.create_index("ix_sightings_player_id", "sightings", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_sightings_player_id", table_name="sightings")
    op.drop_index("ix_sightings_server_name", table_name="sightings")
    op.drop_table("sightings")
    op.drop_index("ix_players_tribe", table_name="players")
    op.drop_column("players", "tribe")
    op.drop_column("players", "status")

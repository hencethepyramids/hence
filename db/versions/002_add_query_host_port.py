"""Add query_host and query_port to servers

Revision ID: 002
Revises: 001
Create Date: 2026-04-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("servers", sa.Column("query_host", sa.String(256), nullable=True))
    op.add_column("servers", sa.Column("query_port", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("servers", "query_port")
    op.drop_column("servers", "query_host")

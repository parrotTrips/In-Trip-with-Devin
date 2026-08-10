"""add is_anonymous to trip_announcements

Revision ID: 20260713_0019
Revises: 20260708_0018
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa

revision = "20260713_0019"
down_revision = "20260708_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trip_announcements", sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("trip_announcements", "is_anonymous")

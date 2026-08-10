"""add photo_url and bio to trip_staff

Revision ID: 20260702_0013
Revises: 20260702_0012
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa

revision = "20260702_0013"
down_revision = "20260702_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trip_staff", sa.Column("photo_url", sa.Text(), nullable=True))
    op.add_column("trip_staff", sa.Column("bio", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("trip_staff", "bio")
    op.drop_column("trip_staff", "photo_url")

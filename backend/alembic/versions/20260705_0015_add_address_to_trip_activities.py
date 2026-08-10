"""add address to trip_activities

Revision ID: 20260705_0015
Revises: 20260705_0014
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa

revision = "20260705_0015"
down_revision = "20260705_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trip_activities", sa.Column("address", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("trip_activities", "address")

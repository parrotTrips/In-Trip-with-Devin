"""add rich fields to trip_recommendations

Revision ID: 20260810_0020
Revises: 20260713_0019
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa

revision = "20260810_0020"
down_revision = "20260713_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trip_recommendations", sa.Column("category", sa.Text(), nullable=True))
    op.add_column("trip_recommendations", sa.Column("neighborhood", sa.Text(), nullable=True))
    op.add_column("trip_recommendations", sa.Column("location", sa.Text(), nullable=True))
    op.add_column("trip_recommendations", sa.Column("highlight", sa.Text(), nullable=True))
    op.add_column("trip_recommendations", sa.Column("price_range", sa.Text(), nullable=True))
    op.add_column("trip_recommendations", sa.Column("rating", sa.Numeric(3, 1), nullable=True))
    op.add_column("trip_recommendations", sa.Column("map_url", sa.Text(), nullable=True))
    op.add_column("trip_recommendations", sa.Column("emoji", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("trip_recommendations", "emoji")
    op.drop_column("trip_recommendations", "map_url")
    op.drop_column("trip_recommendations", "rating")
    op.drop_column("trip_recommendations", "price_range")
    op.drop_column("trip_recommendations", "highlight")
    op.drop_column("trip_recommendations", "location")
    op.drop_column("trip_recommendations", "neighborhood")
    op.drop_column("trip_recommendations", "category")

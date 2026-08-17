"""add contact fields to trip_recommendations

Revision ID: 20260817_0023
Revises: 20260816_0022
Create Date: 2026-08-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260817_0023"
down_revision = "20260816_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trip_recommendations", sa.Column("phone", sa.Text(), nullable=True))
    op.add_column("trip_recommendations", sa.Column("whatsapp_url", sa.Text(), nullable=True))
    op.add_column("trip_recommendations", sa.Column("contact_label", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("trip_recommendations", "contact_label")
    op.drop_column("trip_recommendations", "whatsapp_url")
    op.drop_column("trip_recommendations", "phone")

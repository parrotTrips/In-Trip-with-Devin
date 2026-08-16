"""add traveler app feedback

Revision ID: 20260816_0022
Revises: 20260816_0021
Create Date: 2026-08-16
"""

from alembic import op
import sqlalchemy as sa

revision = "20260816_0022"
down_revision = "20260816_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "traveler_app_feedback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("trip_traveler_id", sa.UUID(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["trip_traveler_id"], ["trip_travelers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trip_traveler_id", name="uq_traveler_app_feedback_trip_traveler_id"),
    )
    op.create_index(
        "ix_traveler_app_feedback_trip_traveler_id",
        "traveler_app_feedback",
        ["trip_traveler_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_traveler_app_feedback_trip_traveler_id", table_name="traveler_app_feedback")
    op.drop_table("traveler_app_feedback")

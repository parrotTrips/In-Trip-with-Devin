"""allow multiple traveler app feedback submissions

Revision ID: 20260827_0024
Revises: 20260817_0023
Create Date: 2026-08-27
"""

from alembic import op

revision = "20260827_0024"
down_revision = "20260817_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_traveler_app_feedback_trip_traveler_id",
        "traveler_app_feedback",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_traveler_app_feedback_trip_traveler_id",
        "traveler_app_feedback",
        ["trip_traveler_id"],
    )

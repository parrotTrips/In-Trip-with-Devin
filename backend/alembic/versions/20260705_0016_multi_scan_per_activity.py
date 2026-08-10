"""multi-scan per activity: add max_checkins to activities, scan_number to checkins, drop unique constraint

Revision ID: 20260705_0016
Revises: 20260705_0015
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa

revision = "20260705_0016"
down_revision = "20260705_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add max_checkins to trip_activities (default 1 = current behavior)
    op.add_column("trip_activities", sa.Column("max_checkins", sa.Integer(), nullable=False, server_default="1"))

    # Add scan_number to activity_checkins
    op.add_column("activity_checkins", sa.Column("scan_number", sa.Integer(), nullable=False, server_default="1"))

    # Drop unique constraint that prevented multiple scans per traveler per activity
    op.drop_constraint("uq_activity_checkins_trip_activity_id", "activity_checkins", type_="unique")

    # Add new unique constraint: one row per (activity, traveler, scan_number)
    op.create_unique_constraint(
        "uq_activity_checkins_activity_traveler_step",
        "activity_checkins",
        ["trip_activity_id", "trip_traveler_id", "scan_number"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_activity_checkins_activity_traveler_step", "activity_checkins", type_="unique")
    op.create_unique_constraint(
        "uq_activity_checkins_trip_activity_id",
        "activity_checkins",
        ["trip_activity_id", "trip_traveler_id"],
    )
    op.drop_column("activity_checkins", "scan_number")
    op.drop_column("trip_activities", "max_checkins")

"""add trip_activity_id to staff_tasks

Revision ID: 20260618_0009
Revises: 20260612_0008
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260618_0009"
down_revision = "20260612_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "staff_tasks",
        sa.Column("trip_activity_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_staff_tasks_trip_activity_id_trip_activities",
        "staff_tasks",
        "trip_activities",
        ["trip_activity_id"],
        ["id"],
    )
    op.create_index(
        "ix_staff_tasks_trip_activity_assignee",
        "staff_tasks",
        ["trip_activity_id", "assigned_to_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_staff_tasks_trip_activity_assignee", table_name="staff_tasks")
    op.drop_constraint(
        "fk_staff_tasks_trip_activity_id_trip_activities",
        "staff_tasks",
        type_="foreignkey",
    )
    op.drop_column("staff_tasks", "trip_activity_id")

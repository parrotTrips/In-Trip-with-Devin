"""add role and staff tables

Revision ID: 20260520_0002
Revises: 20260407_0001
Create Date: 2026-05-20 00:02:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260520_0002"
down_revision = "20260407_0001"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.Text(), nullable=False, server_default="traveler"),
    )

    op.create_table(
        "trip_staff",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("function", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], name=op.f("fk_trip_staff_trip_id_trips")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_trip_staff_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trip_staff")),
        sa.UniqueConstraint("trip_id", "user_id", name=op.f("uq_trip_staff_trip_id")),
    )

    op.create_table(
        "staff_tasks",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_phase_id", UUID, nullable=False),
        sa.Column("assigned_to_user_id", UUID, nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", TIMESTAMPTZ, nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["trip_phase_id"], ["trip_phases.id"], name=op.f("fk_staff_tasks_trip_phase_id_trip_phases")),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], name=op.f("fk_staff_tasks_assigned_to_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_staff_tasks")),
    )


def downgrade() -> None:
    op.drop_table("staff_tasks")
    op.drop_table("trip_staff")
    op.drop_column("users", "role")

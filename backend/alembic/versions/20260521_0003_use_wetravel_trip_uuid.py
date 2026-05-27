"""replace trip_id FK with wetravel_trip_uuid text, drop trips and traveler_products

Revision ID: 20260521_0003
Revises: 20260520_0002
Create Date: 2026-05-21 00:03:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260521_0003"
down_revision = "20260520_0002"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    # Drop trip_staff (migration 0002 created it with trip_id FK → trips)
    op.drop_table("staff_tasks")
    op.drop_table("trip_staff")

    # --- trip_travelers ---
    op.drop_constraint("fk_trip_travelers_trip_id_trips", "trip_travelers", type_="foreignkey")
    op.drop_constraint("uq_trip_travelers_trip_id", "trip_travelers", type_="unique")
    op.drop_column("trip_travelers", "trip_id")
    op.add_column("trip_travelers", sa.Column("wetravel_trip_uuid", sa.Text(), nullable=False, server_default=""))
    op.alter_column("trip_travelers", "wetravel_trip_uuid", server_default=None)
    op.create_unique_constraint(
        "uq_trip_travelers_wetravel_trip_uuid",
        "trip_travelers",
        ["wetravel_trip_uuid", "user_id"],
    )

    # --- trip_phases ---
    op.drop_constraint("fk_trip_phases_trip_id_trips", "trip_phases", type_="foreignkey")
    op.drop_column("trip_phases", "trip_id")
    op.add_column("trip_phases", sa.Column("wetravel_trip_uuid", sa.Text(), nullable=False, server_default=""))
    op.alter_column("trip_phases", "wetravel_trip_uuid", server_default=None)

    # --- traveler_products ---
    op.drop_table("traveler_products")

    # --- trips ---
    op.drop_table("trips")

    # --- recreate trip_staff with wetravel_trip_uuid ---
    op.create_table(
        "trip_staff",
        sa.Column("id", UUID, nullable=False),
        sa.Column("wetravel_trip_uuid", sa.Text(), nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("function", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_trip_staff_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_trip_staff"),
        sa.UniqueConstraint("wetravel_trip_uuid", "user_id", name="uq_trip_staff_wetravel_trip_uuid"),
    )

    # --- recreate staff_tasks ---
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
        sa.ForeignKeyConstraint(
            ["trip_phase_id"], ["trip_phases.id"],
            name="fk_staff_tasks_trip_phase_id_trip_phases",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_user_id"], ["users.id"],
            name="fk_staff_tasks_assigned_to_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_staff_tasks"),
    )


def downgrade() -> None:
    # This migration is not meant to be reversed in production.
    pass

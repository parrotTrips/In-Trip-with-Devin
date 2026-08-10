"""add trip_faqs and trip_cancellation_policies

Revision ID: 20260708_0018
Revises: 20260708_0017
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260708_0018"
down_revision = "20260708_0017"
branch_labels = None
depends_on = None

TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "trip_faqs",
        sa.Column("id", UUID, nullable=False),
        sa.Column("wetravel_trip_uuid", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_faqs_trip_uuid", "trip_faqs", ["wetravel_trip_uuid"])

    op.create_table(
        "trip_cancellation_policies",
        sa.Column("id", UUID, nullable=False),
        sa.Column("wetravel_trip_uuid", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_cancellation_policies_trip_uuid", "trip_cancellation_policies", ["wetravel_trip_uuid"])


def downgrade() -> None:
    op.drop_index("ix_trip_cancellation_policies_trip_uuid", table_name="trip_cancellation_policies")
    op.drop_table("trip_cancellation_policies")
    op.drop_index("ix_trip_faqs_trip_uuid", table_name="trip_faqs")
    op.drop_table("trip_faqs")

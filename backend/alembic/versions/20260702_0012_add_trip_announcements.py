"""add trip_announcements

Revision ID: 20260702_0012
Revises: 20260624_0011
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260702_0012"
down_revision = "20260624_0011"
branch_labels = None
depends_on = None

TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "trip_announcements",
        sa.Column("id", UUID, nullable=False),
        sa.Column("wetravel_trip_uuid", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sent_by_user_id", UUID, nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["sent_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_announcements_trip_uuid", "trip_announcements", ["wetravel_trip_uuid"])


def downgrade() -> None:
    op.drop_index("ix_trip_announcements_trip_uuid", table_name="trip_announcements")
    op.drop_table("trip_announcements")

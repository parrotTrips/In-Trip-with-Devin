"""add trip announcement reads

Revision ID: 20260816_0021
Revises: 20260810_0020
Create Date: 2026-08-16
"""

from alembic import op
import sqlalchemy as sa

revision = "20260816_0021"
down_revision = "20260810_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trip_announcement_reads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("announcement_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["announcement_id"], ["trip_announcements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("announcement_id", "user_id", name="uq_trip_announcement_reads_announcement_user"),
    )
    op.create_index(
        "ix_trip_announcement_reads_announcement_id",
        "trip_announcement_reads",
        ["announcement_id"],
    )
    op.create_index("ix_trip_announcement_reads_user_id", "trip_announcement_reads", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_trip_announcement_reads_user_id", table_name="trip_announcement_reads")
    op.drop_index("ix_trip_announcement_reads_announcement_id", table_name="trip_announcement_reads")
    op.drop_table("trip_announcement_reads")

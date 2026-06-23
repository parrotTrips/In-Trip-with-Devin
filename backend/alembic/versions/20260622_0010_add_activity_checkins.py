"""add activity checkins

Revision ID: 20260622_0010
Revises: 20260618_0009
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260622_0010"
down_revision = "20260618_0009"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "activity_checkins",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_activity_id", UUID, nullable=False),
        sa.Column("trip_traveler_id", UUID, nullable=False),
        sa.Column("scanned_by_user_id", UUID, nullable=False),
        sa.Column(
            "checked_in_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_activity_id"],
            ["trip_activities.id"],
            name=op.f("fk_activity_checkins_trip_activity_id_trip_activities"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_traveler_id"],
            ["trip_travelers.id"],
            name=op.f("fk_activity_checkins_trip_traveler_id_trip_travelers"),
        ),
        sa.ForeignKeyConstraint(
            ["scanned_by_user_id"],
            ["users.id"],
            name=op.f("fk_activity_checkins_scanned_by_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity_checkins")),
        sa.UniqueConstraint(
            "trip_activity_id",
            "trip_traveler_id",
            name=op.f("uq_activity_checkins_trip_activity_id"),
        ),
    )
    op.create_index(
        "ix_activity_checkins_trip_activity_id",
        "activity_checkins",
        ["trip_activity_id"],
    )
    op.create_index(
        "ix_activity_checkins_trip_traveler_id",
        "activity_checkins",
        ["trip_traveler_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_activity_checkins_trip_traveler_id",
        table_name="activity_checkins",
    )
    op.drop_index(
        "ix_activity_checkins_trip_activity_id",
        table_name="activity_checkins",
    )
    op.drop_table("activity_checkins")

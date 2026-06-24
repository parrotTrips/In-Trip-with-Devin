"""add activity participants and scan events

Revision ID: 20260624_0011
Revises: 20260622_0010
Create Date: 2026-06-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260624_0011"
down_revision = "20260622_0010"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "activity_participants",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_activity_id", UUID, nullable=False),
        sa.Column("trip_traveler_id", UUID, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["trip_activity_id"],
            ["trip_activities.id"],
            name=op.f("fk_activity_participants_trip_activity_id_trip_activities"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_traveler_id"],
            ["trip_travelers.id"],
            name=op.f("fk_activity_participants_trip_traveler_id_trip_travelers"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity_participants")),
        sa.UniqueConstraint(
            "trip_activity_id",
            "trip_traveler_id",
            name=op.f("uq_activity_participants_trip_activity_id"),
        ),
    )
    op.create_index(
        "ix_activity_participants_trip_activity_id",
        "activity_participants",
        ["trip_activity_id"],
    )
    op.create_index(
        "ix_activity_participants_trip_traveler_id",
        "activity_participants",
        ["trip_traveler_id"],
    )

    op.create_table(
        "activity_checkin_scan_events",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_activity_id", UUID, nullable=True),
        sa.Column("trip_traveler_id", UUID, nullable=True),
        sa.Column("scanned_by_user_id", UUID, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("raw_payload_hash", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["trip_activity_id"],
            ["trip_activities.id"],
            name=op.f("fk_activity_checkin_scan_events_trip_activity_id_trip_activities"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_traveler_id"],
            ["trip_travelers.id"],
            name=op.f("fk_activity_checkin_scan_events_trip_traveler_id_trip_travelers"),
        ),
        sa.ForeignKeyConstraint(
            ["scanned_by_user_id"],
            ["users.id"],
            name=op.f("fk_activity_checkin_scan_events_scanned_by_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity_checkin_scan_events")),
    )
    op.create_index(
        "ix_activity_checkin_scan_events_trip_activity_id",
        "activity_checkin_scan_events",
        ["trip_activity_id"],
    )
    op.create_index(
        "ix_activity_checkin_scan_events_trip_traveler_id",
        "activity_checkin_scan_events",
        ["trip_traveler_id"],
    )
    op.create_index(
        "ix_activity_checkin_scan_events_scanned_by_user_id",
        "activity_checkin_scan_events",
        ["scanned_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_activity_checkin_scan_events_scanned_by_user_id",
        table_name="activity_checkin_scan_events",
    )
    op.drop_index(
        "ix_activity_checkin_scan_events_trip_traveler_id",
        table_name="activity_checkin_scan_events",
    )
    op.drop_index(
        "ix_activity_checkin_scan_events_trip_activity_id",
        table_name="activity_checkin_scan_events",
    )
    op.drop_table("activity_checkin_scan_events")
    op.drop_index(
        "ix_activity_participants_trip_traveler_id",
        table_name="activity_participants",
    )
    op.drop_index(
        "ix_activity_participants_trip_activity_id",
        table_name="activity_participants",
    )
    op.drop_table("activity_participants")

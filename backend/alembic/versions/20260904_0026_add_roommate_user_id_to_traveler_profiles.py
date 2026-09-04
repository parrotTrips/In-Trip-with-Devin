"""add roommate user id to traveler profiles

Revision ID: 20260904_0026
Revises: 20260902_0025
Create Date: 2026-09-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260904_0026"
down_revision = "20260902_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "traveler_profiles",
        sa.Column("roommate_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_traveler_profiles_roommate_user_id_users",
        "traveler_profiles",
        "users",
        ["roommate_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_traveler_profiles_roommate_user_id_users",
        "traveler_profiles",
        type_="foreignkey",
    )
    op.drop_column("traveler_profiles", "roommate_user_id")

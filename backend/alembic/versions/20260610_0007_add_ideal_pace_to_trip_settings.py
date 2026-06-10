"""add ideal_pace_phase_id to trip_settings

Revision ID: 20260610_0007
Revises: 20260610_0006
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = '20260610_0007'
down_revision = '20260610_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'trip_settings',
        sa.Column('ideal_pace_phase_id', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('trip_settings', 'ideal_pace_phase_id')

"""move service_agreement_url from traveler_profiles to wetravel_trips

Revision ID: 20260610_0006
Revises: 20260602_0005
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = '20260610_0006'
down_revision = '20260602_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # wetravel_trips is created by the WeTravel sync script, not by Alembic.
    # Ensure it exists so this migration is safe to run on a fresh test database.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wetravel_trips (
            trip_uuid TEXT PRIMARY KEY,
            title TEXT,
            destination TEXT,
            start_date DATE,
            end_date DATE,
            url TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.add_column(
        'wetravel_trips',
        sa.Column('service_agreement_url', sa.Text(), nullable=True),
    )
    op.drop_column('traveler_profiles', 'service_agreement_url')


def downgrade() -> None:
    op.add_column(
        'traveler_profiles',
        sa.Column('service_agreement_url', sa.Text(), nullable=True),
    )
    op.drop_column('wetravel_trips', 'service_agreement_url')

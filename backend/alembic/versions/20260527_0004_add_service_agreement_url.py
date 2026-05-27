"""add service_agreement_url to traveler_profiles

Revision ID: 20260527_0004
Revises: 20260521_0003
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = '20260527_0004'
down_revision = '20260521_0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'traveler_profiles',
        sa.Column('service_agreement_url', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('traveler_profiles', 'service_agreement_url')

"""add trip_settings table

Revision ID: 20260602_0005
Revises: 20260527_0004
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260602_0005'
down_revision = '20260527_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'trip_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('trip_uuid', sa.Text(), nullable=False),
        sa.Column('mode', sa.Text(), nullable=False, server_default='pre-trip'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('trip_uuid', name='uq_trip_settings_trip_uuid'),
    )
    op.create_index('ix_trip_settings_trip_uuid', 'trip_settings', ['trip_uuid'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_trip_settings_trip_uuid', 'trip_settings')
    op.drop_table('trip_settings')

"""add trip_contacts table

Revision ID: 20260612_0008
Revises: 20260610_0007
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '20260612_0008'
down_revision = '20260610_0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'trip_contacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('wetravel_trip_uuid', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_trip_contacts_trip_uuid', 'trip_contacts', ['wetravel_trip_uuid'])


def downgrade() -> None:
    op.drop_index('ix_trip_contacts_trip_uuid', 'trip_contacts')
    op.drop_table('trip_contacts')

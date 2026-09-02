"""add pre departure profile fields

Revision ID: 20260902_0025
Revises: 20260827_0024
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa

revision = "20260902_0025"
down_revision = "20260827_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("traveler_profiles", sa.Column("visa_status", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("arrival_date", sa.Date(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("arrival_time", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("arrival_flight", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("departure_date", sa.Date(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("departure_time", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("departure_flight", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("checked_bags", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("travel_insurance_status", sa.Text(), nullable=True))
    op.add_column(
        "traveler_profiles",
        sa.Column("travel_insurance_brazil_medical_coverage", sa.Text(), nullable=True),
    )
    op.add_column("traveler_profiles", sa.Column("travel_insurance_provider", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("travel_insurance_policy_number", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("travel_insurance_notes", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("roommate_status", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("roommate_email", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("room_configuration", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("roommate_gender_preference", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("extended_stay_help", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("extended_stay_help_details", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("early_check_in_preference", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("emergency_contact", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("instagram_handle", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("trip_mood", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("social_topic", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("always_up_for", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("home_address", sa.Text(), nullable=True))
    op.add_column("traveler_profiles", sa.Column("final_considerations", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("traveler_profiles", "final_considerations")
    op.drop_column("traveler_profiles", "home_address")
    op.drop_column("traveler_profiles", "always_up_for")
    op.drop_column("traveler_profiles", "social_topic")
    op.drop_column("traveler_profiles", "trip_mood")
    op.drop_column("traveler_profiles", "instagram_handle")
    op.drop_column("traveler_profiles", "emergency_contact")
    op.drop_column("traveler_profiles", "early_check_in_preference")
    op.drop_column("traveler_profiles", "extended_stay_help_details")
    op.drop_column("traveler_profiles", "extended_stay_help")
    op.drop_column("traveler_profiles", "roommate_gender_preference")
    op.drop_column("traveler_profiles", "room_configuration")
    op.drop_column("traveler_profiles", "roommate_email")
    op.drop_column("traveler_profiles", "roommate_status")
    op.drop_column("traveler_profiles", "travel_insurance_notes")
    op.drop_column("traveler_profiles", "travel_insurance_policy_number")
    op.drop_column("traveler_profiles", "travel_insurance_provider")
    op.drop_column("traveler_profiles", "travel_insurance_brazil_medical_coverage")
    op.drop_column("traveler_profiles", "travel_insurance_status")
    op.drop_column("traveler_profiles", "checked_bags")
    op.drop_column("traveler_profiles", "departure_flight")
    op.drop_column("traveler_profiles", "departure_time")
    op.drop_column("traveler_profiles", "departure_date")
    op.drop_column("traveler_profiles", "arrival_flight")
    op.drop_column("traveler_profiles", "arrival_time")
    op.drop_column("traveler_profiles", "arrival_date")
    op.drop_column("traveler_profiles", "visa_status")

"""initial schema

Revision ID: 20260407_0001
Revises:
Create Date: 2026-04-07 00:01:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260407_0001"
down_revision = None
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID, nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("phone", name=op.f("uq_users_phone")),
    )
    op.create_table(
        "trips",
        sa.Column("id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("short_name", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trips")),
    )
    op.create_table(
        "media_assets",
        sa.Column("id", UUID, nullable=False),
        sa.Column("drive_file_id", sa.Text(), nullable=False),
        sa.Column("drive_path", sa.Text(), nullable=True),
        sa.Column("public_url", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_assets")),
        sa.UniqueConstraint("drive_file_id", name=op.f("uq_media_assets_drive_file_id")),
    )
    op.create_table(
        "otp_codes",
        sa.Column("id", UUID, nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("expires_at", TIMESTAMPTZ, nullable=False),
        sa.Column(
            "used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_otp_codes")),
    )
    op.create_table(
        "trip_travelers",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], name=op.f("fk_trip_travelers_trip_id_trips")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_trip_travelers_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trip_travelers")),
        sa.UniqueConstraint("trip_id", "user_id", name=op.f("uq_trip_travelers_trip_id")),
    )
    op.create_table(
        "traveler_profiles",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_traveler_id", UUID, nullable=False),
        sa.Column("preferred_name", sa.Text(), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.Text(), nullable=True),
        sa.Column("passport_first_name", sa.Text(), nullable=True),
        sa.Column("passport_last_name", sa.Text(), nullable=True),
        sa.Column("passport_country", sa.Text(), nullable=True),
        sa.Column("passport_number", sa.Text(), nullable=True),
        sa.Column("passport_issue_date", sa.Date(), nullable=True),
        sa.Column("passport_expiration_date", sa.Date(), nullable=True),
        sa.Column("dietary_restrictions_flag", sa.Boolean(), nullable=True),
        sa.Column("dietary_restrictions_details", sa.Text(), nullable=True),
        sa.Column("seasickness_flag", sa.Boolean(), nullable=True),
        sa.Column("plus_one_flag", sa.Boolean(), nullable=True),
        sa.Column("plus_one_name", sa.Text(), nullable=True),
        sa.Column("plus_one_email", sa.Text(), nullable=True),
        sa.Column("needs_flight_help_flag", sa.Boolean(), nullable=True),
        sa.Column("flight_help_details", sa.Text(), nullable=True),
        sa.Column("needs_travel_insurance_help_flag", sa.Boolean(), nullable=True),
        sa.Column("unforgettable_trip_details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_traveler_id"],
            ["trip_travelers.id"],
            name=op.f("fk_traveler_profiles_trip_traveler_id_trip_travelers"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_traveler_profiles")),
        sa.UniqueConstraint(
            "trip_traveler_id",
            name=op.f("uq_traveler_profiles_trip_traveler_id"),
        ),
    )
    op.create_table(
        "traveler_products",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_traveler_id", UUID, nullable=False),
        sa.Column("package_name", sa.Text(), nullable=True),
        sa.Column("room_type", sa.Text(), nullable=True),
        sa.Column("amount_paid_usd", sa.Numeric(12, 2), nullable=True),
        sa.Column("purchased_addons_summary", sa.Text(), nullable=True),
        sa.Column("service_agreement_media_asset_id", UUID, nullable=True),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["service_agreement_media_asset_id"],
            ["media_assets.id"],
            name=op.f(
                "fk_traveler_products_service_agreement_media_asset_id_media_assets"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["trip_traveler_id"],
            ["trip_travelers.id"],
            name=op.f("fk_traveler_products_trip_traveler_id_trip_travelers"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_traveler_products")),
        sa.UniqueConstraint(
            "trip_traveler_id",
            name=op.f("uq_traveler_products_trip_traveler_id"),
        ),
    )
    op.create_table(
        "trip_phases",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_id", UUID, nullable=False),
        sa.Column("parent_phase_id", UUID, nullable=True),
        sa.Column("phase_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("subtitle", sa.Text(), nullable=True),
        sa.Column("icon", sa.Text(), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("detailed_description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("starts_at", TIMESTAMPTZ, nullable=True),
        sa.Column("ends_at", TIMESTAMPTZ, nullable=True),
        sa.Column("is_locked_by_default", sa.Boolean(), nullable=False),
        sa.Column("is_visible", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["parent_phase_id"],
            ["trip_phases.id"],
            name=op.f("fk_trip_phases_parent_phase_id_trip_phases"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            name=op.f("fk_trip_phases_trip_id_trips"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trip_phases")),
    )
    op.create_table(
        "trip_phase_checklist_items",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_phase_id", UUID, nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_phase_id"],
            ["trip_phases.id"],
            name=op.f("fk_trip_phase_checklist_items_trip_phase_id_trip_phases"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trip_phase_checklist_items")),
    )
    op.create_table(
        "trip_phase_links",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_phase_id", UUID, nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_phase_id"],
            ["trip_phases.id"],
            name=op.f("fk_trip_phase_links_trip_phase_id_trip_phases"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trip_phase_links")),
    )
    op.create_table(
        "trip_activities",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_phase_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("activity_type", sa.Text(), nullable=False),
        sa.Column("starts_at", TIMESTAMPTZ, nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("practical_info", sa.Text(), nullable=True),
        sa.Column("amount_brl", sa.Numeric(12, 2), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_phase_id"],
            ["trip_phases.id"],
            name=op.f("fk_trip_activities_trip_phase_id_trip_phases"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trip_activities")),
    )
    op.create_table(
        "activity_media",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_activity_id", UUID, nullable=False),
        sa.Column("media_asset_id", UUID, nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["media_asset_id"],
            ["media_assets.id"],
            name=op.f("fk_activity_media_media_asset_id_media_assets"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_activity_id"],
            ["trip_activities.id"],
            name=op.f("fk_activity_media_trip_activity_id_trip_activities"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity_media")),
    )
    op.create_table(
        "traveler_checklist_progress",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_traveler_id", UUID, nullable=False),
        sa.Column("trip_phase_checklist_item_id", UUID, nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", TIMESTAMPTZ, nullable=True),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_phase_checklist_item_id"],
            ["trip_phase_checklist_items.id"],
            name=op.f(
                "fk_traveler_checklist_progress_trip_phase_checklist_item_id_trip_phase_checklist_items"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["trip_traveler_id"],
            ["trip_travelers.id"],
            name=op.f(
                "fk_traveler_checklist_progress_trip_traveler_id_trip_travelers"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_traveler_checklist_progress")),
        sa.UniqueConstraint(
            "trip_traveler_id",
            "trip_phase_checklist_item_id",
            name=op.f("uq_traveler_checklist_progress_trip_traveler_id"),
        ),
    )
    op.create_table(
        "traveler_phase_progress",
        sa.Column("id", UUID, nullable=False),
        sa.Column("trip_traveler_id", UUID, nullable=False),
        sa.Column("trip_phase_id", UUID, nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", TIMESTAMPTZ, nullable=True),
        sa.Column(
            "updated_at",
            TIMESTAMPTZ,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_phase_id"],
            ["trip_phases.id"],
            name=op.f("fk_traveler_phase_progress_trip_phase_id_trip_phases"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_traveler_id"],
            ["trip_travelers.id"],
            name=op.f("fk_traveler_phase_progress_trip_traveler_id_trip_travelers"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_traveler_phase_progress")),
        sa.UniqueConstraint(
            "trip_traveler_id",
            "trip_phase_id",
            name=op.f("uq_traveler_phase_progress_trip_traveler_id"),
        ),
    )


def downgrade() -> None:
    op.drop_table("traveler_phase_progress")
    op.drop_table("traveler_checklist_progress")
    op.drop_table("activity_media")
    op.drop_table("trip_activities")
    op.drop_table("trip_phase_links")
    op.drop_table("trip_phase_checklist_items")
    op.drop_table("trip_phases")
    op.drop_table("traveler_products")
    op.drop_table("traveler_profiles")
    op.drop_table("trip_travelers")
    op.drop_table("otp_codes")
    op.drop_table("media_assets")
    op.drop_table("trips")
    op.drop_table("users")

"""Expand centre catalogue, staff assignments, payment and audit records.

Revision ID: e282a167dc55
Revises: b71a209cf814
"""
from alembic import op
import sqlalchemy as sa

revision = "e282a167dc55"
down_revision = "b71a209cf814"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("diagnostic_centres", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("diagnostic_centres", sa.Column("state", sa.String(100), nullable=True))
    op.add_column("diagnostic_centres", sa.Column("postal_code", sa.String(20), nullable=True))
    op.add_column("diagnostic_centres", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("diagnostic_centres", sa.Column("opening_hours", sa.JSON(), nullable=True))
    op.add_column("diagnostic_centres", sa.Column("services", sa.JSON(), nullable=True))
    op.add_column("diagnostic_tests", sa.Column("category", sa.String(100), nullable=True))
    op.add_column("diagnostic_tests", sa.Column("sample_type", sa.String(100), nullable=True))
    op.add_column("diagnostic_tests", sa.Column("estimated_report_time_minutes", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("currency", sa.String(3), nullable=False, server_default="INR"))
    op.alter_column("payments", "currency", server_default=None)
    op.create_table(
        "centre_staff",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("centre_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["centre_id"], ["diagnostic_centres.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("centre_id", "user_id", name="uq_centre_staff"),
    )
    op.create_index("ix_centre_staff_centre_id", "centre_staff", ["centre_id"])
    op.create_index("ix_centre_staff_user_id", "centre_staff", ["user_id"])
    op.create_table(
        "booking_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("booking_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("from_status", sa.String(50), nullable=True),
        sa.Column("to_status", sa.String(50), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_booking_events_booking_id", "booking_events", ["booking_id"])
    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_outbox_status", "notification_outbox", ["status"])


def downgrade() -> None:
    op.drop_index("ix_notification_outbox_status", table_name="notification_outbox")
    op.drop_table("notification_outbox")
    op.drop_index("ix_booking_events_booking_id", table_name="booking_events")
    op.drop_table("booking_events")
    op.drop_index("ix_centre_staff_user_id", table_name="centre_staff")
    op.drop_index("ix_centre_staff_centre_id", table_name="centre_staff")
    op.drop_table("centre_staff")
    op.drop_column("payments", "currency")
    op.drop_column("diagnostic_tests", "estimated_report_time_minutes")
    op.drop_column("diagnostic_tests", "sample_type")
    op.drop_column("diagnostic_tests", "category")
    op.drop_column("diagnostic_centres", "services")
    op.drop_column("diagnostic_centres", "opening_hours")
    op.drop_column("diagnostic_centres", "email")
    op.drop_column("diagnostic_centres", "postal_code")
    op.drop_column("diagnostic_centres", "state")
    op.drop_column("diagnostic_centres", "description")

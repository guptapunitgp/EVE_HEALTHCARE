"""Support safe payment retries for a booking.

Revision ID: d4179736aee1
Revises: e282a167dc55
"""
from alembic import op
import sqlalchemy as sa

revision = "d4179736aee1"
down_revision = "e282a167dc55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_payments_booking_id", table_name="payments")
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"], unique=False)
    op.add_column("payments", sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"))
    op.alter_column("payments", "attempt_number", server_default=None)


def downgrade() -> None:
    op.drop_column("payments", "attempt_number")
    op.drop_index("ix_payments_booking_id", table_name="payments")
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"], unique=True)

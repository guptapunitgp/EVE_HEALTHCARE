"""Store timezone per centre for appointment hour validation.

Revision ID: b09f603dc218
Revises: d4179736aee1
"""
from alembic import op
import sqlalchemy as sa

revision = "b09f603dc218"
down_revision = "d4179736aee1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("diagnostic_centres", sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Kolkata"))
    op.alter_column("diagnostic_centres", "timezone", server_default=None)


def downgrade() -> None:
    op.drop_column("diagnostic_centres", "timezone")

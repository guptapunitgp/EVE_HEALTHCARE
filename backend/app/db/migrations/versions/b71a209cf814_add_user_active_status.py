"""Add user active status for account suspension.

Revision ID: b71a209cf814
Revises: 2320f85032b4
"""
from alembic import op
import sqlalchemy as sa

revision = "b71a209cf814"
down_revision = "2320f85032b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("users", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "is_active")

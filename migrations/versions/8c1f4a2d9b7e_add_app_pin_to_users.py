"""add app pin to users

Revision ID: 8c1f4a2d9b7e
Revises: 7f3c2b9e4d6
"""
from alembic import op
import sqlalchemy as sa

revision = "8c1f4a2d9b7e"
down_revision = "7f3c2b9e4d6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("app_pin_hash", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("users", "app_pin_hash")

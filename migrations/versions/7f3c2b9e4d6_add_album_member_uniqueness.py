"""Prevent duplicate album memberships

Revision ID: 7f3c2b9e4d6
Revises: 5e0d3d4f8a1
"""
from alembic import op

revision = "7f3c2b9e4d6"
down_revision = "5e0d3d4f8a1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DELETE FROM album_members a
        USING album_members b
        WHERE a.id > b.id
          AND a.album_id = b.album_id
          AND a.user_id = b.user_id
    """)

    op.create_unique_constraint(
        "uq_album_members_album_user",
        "album_members",
        ["album_id", "user_id"],
    )


def downgrade():
    op.drop_constraint(
        "uq_album_members_album_user",
        "album_members",
        type_="unique",
    )

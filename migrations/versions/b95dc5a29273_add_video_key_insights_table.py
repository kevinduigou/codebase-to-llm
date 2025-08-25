"""add video key insights table

Revision ID: b95dc5a29273
Revises: 71e8e4523f28
Create Date: 2025-08-20 13:19:47.123456

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b95dc5a29273"
down_revision = "71e8e4523f28"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_key_insights",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("key_insights_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("video_key_insights")

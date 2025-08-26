"""add video summary table

Revision ID: c3d4e5f67890
Revises: b95dc5a29273
Create Date: 2025-09-20 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c3d4e5f67890"
down_revision = "b95dc5a29273"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_summaries",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("segments_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("video_summaries")

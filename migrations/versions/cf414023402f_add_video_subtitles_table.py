"""add video subtitles table

Revision ID: cf414023402f
Revises: c3d4e5f67890
Create Date: 2025-08-27 17:09:57.959743

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cf414023402f"
down_revision = "c3d4e5f67890"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_subtitles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("video_file_id", sa.String(), nullable=False),
        sa.Column("subtitle_file_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("video_subtitles")

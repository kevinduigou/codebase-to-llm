"""add files and directories tables"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0c4e1b38f3f4"
down_revision = "ebcef345da55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "directories",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "files",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("directory_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("files")
    op.drop_table("directories")

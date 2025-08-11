"""add models table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0a1b2c3d4e5f"
down_revision = "ebcef345da55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "models",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("api_key_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("models")

"""add email and validation columns to users"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ebcef345da55"
down_revision = "5fc23dc1d6d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "validated", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.add_column("users", sa.Column("validation_token", sa.String(), nullable=True))
    op.execute("UPDATE users SET email='', validated=true, validation_token=''")
    op.alter_column("users", "email", nullable=False)
    op.alter_column("users", "validation_token", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "validation_token")
    op.drop_column("users", "validated")
    op.drop_column("users", "email")

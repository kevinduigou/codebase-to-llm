"""merge heads

Revision ID: 71e8e4523f28
Revises: 0a1b2c3d4e5f, 0c4e1b38f3f4
Create Date: 2025-08-13 09:47:15.923461

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "71e8e4523f28"
down_revision = ("0a1b2c3d4e5f", "0c4e1b38f3f4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

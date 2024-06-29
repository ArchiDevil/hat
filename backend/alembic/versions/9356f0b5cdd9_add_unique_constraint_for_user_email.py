"""Add unique constraint for user email

Revision ID: 9356f0b5cdd9
Revises: 94eb09ac97fe
Create Date: 2024-06-21 20:43:53.483289

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "9356f0b5cdd9"
down_revision: Union[str, None] = "94eb09ac97fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("user_email_key", "user", ["email"])


def downgrade() -> None:
    op.drop_constraint("user_email_key", "user", type_="unique")

"""Added tasks generation

Revision ID: f83699ff2dd0
Revises: 004d29805949
Create Date: 2024-03-25 23:56:06.617218

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "f83699ff2dd0"
down_revision: Union[str, None] = "004d29805949"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("document_task")

"""Add registration token table

Revision ID: fc5e85011fea
Revises: 4f5e0c85ccda
Create Date: 2026-03-27 20:47:14.014590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'fc5e85011fea'
down_revision: Union[str, None] = '4f5e0c85ccda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "registration_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
    )


def downgrade() -> None:
    op.drop_table("registration_token")

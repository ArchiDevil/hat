"""Add record comment table

Revision ID: 32d5a77e6615
Revises: 9bb8ccd3ee99
Create Date: 2025-11-30 20:42:40.011040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '32d5a77e6615'
down_revision: Union[str, None] = '9bb8ccd3ee99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "record_comment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], ),
        sa.ForeignKeyConstraint(["record_id"], ["document_record.id"], ),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("record_comment")

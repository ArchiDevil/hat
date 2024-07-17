"""Add links between xliff and tmx

Revision ID: d78c74ab226b
Revises: b3e764c93fac
Create Date: 2024-07-17 01:03:39.274777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'd78c74ab226b'
down_revision: Union[str, None] = '6d107741a92e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('xliff_record_to_tmx',
        sa.Column('xliff_id', sa.Integer(), nullable=False),
        sa.Column('tmx_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tmx_id'], ['tmx_document.id'], ),
        sa.ForeignKeyConstraint(['xliff_id'], ['xliff_document.id'], )
    )


def downgrade() -> None:
    op.drop_table('xliff_record_to_tmx')

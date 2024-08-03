"""Add text document types

Revision ID: 182d14227dee
Revises: baa325f58df6
Create Date: 2024-08-03 21:12:10.777437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '182d14227dee'
down_revision: Union[str, None] = 'baa325f58df6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('txt_document',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('original_document', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['document.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('txt_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('offset', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['txt_document.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['document_record.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('txt_record')
    op.drop_table('txt_document')

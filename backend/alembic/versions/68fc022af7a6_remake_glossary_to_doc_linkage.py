"""Remake glossary to doc linkage

Revision ID: 68fc022af7a6
Revises: 3249385a213d
Create Date: 2025-01-11 19:42:37.967166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '68fc022af7a6'
down_revision: Union[str, None] = '3249385a213d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('glossary_to_document', 'document_id',
               existing_type=sa.Integer(),
               nullable=False)
    op.alter_column('glossary_to_document', 'glossary_id',
               existing_type=sa.Integer(),
               nullable=False)
    op.drop_column('glossary_to_document', 'id')
    op.create_primary_key('pk_glossary_to_document', 'glossary_to_document', ['glossary_id', 'document_id'])


def downgrade() -> None:
    op.drop_constraint('pk_glossary_to_document', 'glossary_to_document')
    op.add_column('glossary_to_document', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False))
    op.alter_column('glossary_to_document', 'glossary_id',
               existing_type=sa.Integer(),
               nullable=True)
    op.alter_column('glossary_to_document', 'document_id',
               existing_type=sa.Integer(),
               nullable=True)

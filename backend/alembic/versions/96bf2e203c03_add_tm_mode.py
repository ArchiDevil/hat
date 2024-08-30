"""Add TM mode

Revision ID: 96bf2e203c03
Revises: bc813d99ccfb
Create Date: 2024-08-13 15:36:39.282152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '96bf2e203c03'
down_revision: Union[str, None] = 'bc813d99ccfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

modetype = sa.Enum('read', 'write', name='tmmode')



def upgrade() -> None:
    modetype.create(op.get_bind(), checkfirst=True)
    op.add_column('document_to_translation_memory', sa.Column('mode', modetype, nullable=True))
    op.execute(sa.update(sa.table('document_to_translation_memory', sa.Column('mode'))).values(mode='read'))
    op.alter_column('document_to_translation_memory', 'mode', nullable=False)
    op.create_primary_key(None, 'document_to_translation_memory', ['doc_id', 'tm_id', 'mode'])


def downgrade() -> None:
    op.drop_column('document_to_translation_memory', 'mode')
    modetype.drop(op.get_bind())

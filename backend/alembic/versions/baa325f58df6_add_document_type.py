"""Add document type

Revision ID: baa325f58df6
Revises: b751dedd829b
Create Date: 2024-08-03 20:20:19.620476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'baa325f58df6'
down_revision: Union[str, None] = 'b751dedd829b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


documentype = sa.Enum('xliff', 'txt', name='documenttype')

def upgrade() -> None:
    documentype.create(op.get_bind(), checkfirst=True)
    op.add_column('document', sa.Column('type', documentype))
    op.execute("UPDATE document SET type = 'xliff'")
    op.alter_column('document', 'type', nullable=False)


def downgrade() -> None:
    op.drop_column('document', 'type')
    documentype.drop(op.get_bind(), checkfirst=True)

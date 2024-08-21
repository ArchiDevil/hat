"""Enable n-grams extension

Revision ID: 15355f38c714
Revises: b3e764c93fac
Create Date: 2024-07-16 22:14:21.734202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '15355f38c714'
down_revision: Union[str, None] = 'd78c74ab226b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.create_index(
        'trgm_tmx_src_idx',
        'tmx_record',
        ['source'],
        postgresql_ops={'source': 'gist_trgm_ops'},
        unique=False,
        postgresql_using='gist'
    )


def downgrade() -> None:
    op.drop_index('trgm_tmx_src_idx', 'tmx_record')
    op.execute('DROP EXTENSION pg_trgm')

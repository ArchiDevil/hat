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
    op.execute('CREATE EXTENSION pg_trgm')
    op.execute('CREATE INDEX trgm_tmx_src_idx ON tmx_record USING gist (source gist_trgm_ops)')

def downgrade() -> None:
    op.execute('DROP INDEX trgm_tmx_src_idx')
    op.execute('DROP EXTENSION pg_trgm')

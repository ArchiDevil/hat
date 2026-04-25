"""Remove state field from XLIFF records

Revision ID: f8719b5ebefe
Revises: 56cc00f2d285
Create Date: 2026-04-19 18:13:16.398511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'f8719b5ebefe'
down_revision: Union[str, None] = '56cc00f2d285'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('xliff_record', 'state')


def downgrade() -> None:
    op.add_column(
        'xliff_record',
        sa.Column(
            'state', sa.String(), nullable=True
        )
    )
    op.execute(
        sa.update(
            sa.table('xliff_record', sa.Column('state'))
        ).values('needs-translation')
    )
    op.alter_column('xliff_record', 'state', nullable=False)

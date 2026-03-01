"""Make project_id nullable in document

Revision ID: 35020a30cb48
Revises: dcd734dfe9c4
Create Date: 2026-03-01 15:05:44.684815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '35020a30cb48'
down_revision: Union[str, None] = 'dcd734dfe9c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('document', 'project_id',
               existing_type=sa.INTEGER(),
               nullable=False)


def downgrade() -> None:
    op.alter_column('document', 'project_id',
               existing_type=sa.INTEGER(),
               nullable=True)

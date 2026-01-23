"""Remove segment source

Revision ID: c12df3eda4a2
Revises: 45eb3f99d065
Create Date: 2026-01-23 21:51:07.858781

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'c12df3eda4a2'
down_revision: Union[str, None] = '45eb3f99d065'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

recordsource = sa.Enum(
    "glossary",
    "machine_translation",
    "translation_memory",
    "full_match",
    name="recordsource",
)


def upgrade() -> None:
    op.drop_column('document_record', 'target_source')
    recordsource.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    recordsource.create(op.get_bind(), checkfirst=True)
    op.add_column('document_record', sa.Column('target_source', recordsource, autoincrement=False, nullable=True))

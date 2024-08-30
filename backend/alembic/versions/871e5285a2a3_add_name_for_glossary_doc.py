"""Add name for glossary_document

Revision ID: 871e5285a2a3
Revises: bc813d99ccfb
Create Date: 2024-08-15 22:11:42.150076

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# pylint: disable=E1101

revision: str = "871e5285a2a3"
down_revision: Union[str, None] = "96bf2e203c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("glossary_document", sa.Column("name", sa.String()))
    op.execute(sa.update(sa.table("glossary_document", sa.column('name'))).values(name='empty'))
    op.alter_column("glossary_document", "name", nullable=False)


def downgrade() -> None:
    op.drop_column("glossary_document", "name")

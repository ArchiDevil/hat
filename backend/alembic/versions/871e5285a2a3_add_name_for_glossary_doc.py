"""add_name_for_glossary_doc

Revision ID: 871e5285a2a3
Revises: bc813d99ccfb
Create Date: 2024-08-15 22:11:42.150076

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "871e5285a2a3"
down_revision: Union[str, None] = "bc813d99ccfb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("glossary_document", sa.Column("name", sa.String(), nullable=False))


def downgrade() -> None:
    op.drop_column("glossary_document", "name")

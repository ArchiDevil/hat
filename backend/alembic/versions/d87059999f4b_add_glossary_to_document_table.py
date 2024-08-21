"""add_glossary_to_document_table

Revision ID: d87059999f4b
Revises: c8d6d3fa5dda
Create Date: 2024-08-21 22:44:06.335799

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d87059999f4b"
down_revision: Union[str, None] = "c8d6d3fa5dda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "glossary_to_document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("glossary_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
        ),
        sa.ForeignKeyConstraint(
            ["glossary_id"],
            ["glossary.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("glossary_to_document")

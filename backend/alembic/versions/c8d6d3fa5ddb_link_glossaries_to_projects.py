"""Link glossaries to projects

Revision ID: c8d6d3fa5ddb
Revises: 35020a30cb48
Create Date: 2026-03-07 19:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "c8d6d3fa5ddb"
down_revision: Union[str, None] = "35020a30cb48"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new project_glossary table
    op.create_table(
        "project_glossary",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("glossary_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["glossary_id"],
            ["glossary.id"],
        ),
        sa.PrimaryKeyConstraint("project_id", "glossary_id"),
    )

    # Drop old glossary_to_document table
    op.drop_table("glossary_to_document")


def downgrade() -> None:
    # Recreate old glossary_to_document table
    op.create_table(
        "glossary_to_document",
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("glossary_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
        ),
        sa.ForeignKeyConstraint(
            ["glossary_id"],
            ["glossary.id"],
        ),
        sa.PrimaryKeyConstraint("document_id", "glossary_id"),
    )

    # Drop new project_glossary table
    op.drop_table("project_glossary")

"""Link translation memories to projects

Revision ID: 4f5e0c85ccda
Revises: c8d6d3fa5ddb
Create Date: 2026-03-08 15:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "4f5e0c85ccda"
down_revision: Union[str, None] = "c8d6d3fa5ddb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

oldmodetype = sa.Enum('read', 'write', name='tmmode')
newmodetype = sa.Enum('read', 'write', name='tmmode', native_enum=False, create_constraint=True)


def upgrade() -> None:
    # Create new project_translation_memory table
    op.create_table(
        "project_translation_memory",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("tm_id", sa.Integer(), nullable=False),
        sa.Column("mode", newmodetype, nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tm_id"],
            ["translation_memory.id"],
        ),
        sa.PrimaryKeyConstraint("project_id", "tm_id", "mode"),
    )

    # Drop old document_to_translation_memory table
    op.drop_table("document_to_translation_memory")
    oldmodetype.drop(op.get_bind())


def downgrade() -> None:
    # Recreate old document_to_translation_memory table
    op.create_table(
        "document_to_translation_memory",
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("tm_id", sa.Integer(), nullable=False),
        sa.Column("mode", oldmodetype, nullable=False),
        sa.ForeignKeyConstraint(
            ["doc_id"],
            ["document.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tm_id"],
            ["translation_memory.id"],
        ),
        sa.PrimaryKeyConstraint("doc_id", "tm_id", "mode"),
    )

    # Drop new project_translation_memory table
    op.drop_table("project_translation_memory")

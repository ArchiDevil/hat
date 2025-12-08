"""Add segment translation source

Revision ID: 3fbb82ea683d
Revises: 32d5a77e6615
Create Date: 2025-12-06 13:49:58.517637

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "3fbb82ea683d"
down_revision: Union[str, None] = "32d5a77e6615"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

segmentsource = sa.Enum(
    "glossary",
    "machine_translation",
    "translation_memory",
    "full_match",
    name="recordsource",
)


def upgrade() -> None:
    segmentsource.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "document_record",
        sa.Column(
            "target_source",
            segmentsource,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("document_record", "target_source")
    segmentsource.drop(op.get_bind(), checkfirst=True)

"""Add word count to document record

Revision ID: 4a5b6c7d8e9f
Revises: 3fbb82ea683d
Create Date: 2026-01-11 15:42:00.000000

"""

from typing import Sequence, Union

from alembic import op, context
import sqlalchemy as sa

from app.linguistic.word_count import count_words


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "4a5b6c7d8e9f"
down_revision: Union[str, None] = "3fbb82ea683d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add word_count column with default value 0
    op.add_column(
        "document_record",
        sa.Column(
            "word_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )

    if not context.is_offline_mode():
        # Populate existing records with calculated word counts
        connection = op.get_bind()
        result = connection.execute(sa.text("SELECT id, source FROM document_record"))
        for record_id, source in result:
            word_count = count_words(source)
            connection.execute(
                sa.text(
                    "UPDATE document_record SET word_count = :word_count WHERE id = :record_id"
                ),
                {"word_count": word_count, "record_id": record_id},
            )


def downgrade() -> None:
    op.drop_column("document_record", "word_count")

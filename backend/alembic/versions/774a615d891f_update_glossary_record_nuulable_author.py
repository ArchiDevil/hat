"""update_glossary_record_nuulable_author

Revision ID: 774a615d891f
Revises: d87059999f4b
Create Date: 2024-09-01 21:31:08.337084

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "774a615d891f"
down_revision: Union[str, None] = "d87059999f4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "glossary_record", "author", existing_type=sa.VARCHAR(), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "glossary_record", "author", existing_type=sa.VARCHAR(), nullable=False
    )

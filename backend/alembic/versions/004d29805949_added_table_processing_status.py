"""Added table processing status

Revision ID: 004d29805949
Revises: ebad9129920d
Create Date: 2024-03-25 23:36:24.242919

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004d29805949"
down_revision: Union[str, None] = "ebad9129920d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("xliff_document", sa.Column("processing_status", sa.String()))
    update = sa.update(
        sa.table("xliff_document", sa.Column("processing_status"))
    ).values(processing_status="done")
    op.execute(update)
    op.alter_column("xliff_document", "processing_status", nullable=False)


def downgrade() -> None:
    op.drop_column("xliff_document", "processing_status")

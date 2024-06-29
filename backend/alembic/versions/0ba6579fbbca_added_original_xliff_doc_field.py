"""Added original XLIFF doc field

Revision ID: 0ba6579fbbca
Revises: d2f116d3976e
Create Date: 2023-12-27 21:17:14.641409

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "0ba6579fbbca"
down_revision: Union[str, None] = "d2f116d3976e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "xliff_document", sa.Column("original_document", sa.String(), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("xliff_document", "original_document")

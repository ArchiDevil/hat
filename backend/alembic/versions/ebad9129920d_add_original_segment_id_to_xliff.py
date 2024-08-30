"""Add original segment id to XLIFF

Revision ID: ebad9129920d
Revises: 0ba6579fbbca
Create Date: 2024-01-02 20:17:06.133690

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "ebad9129920d"
down_revision: Union[str, None] = "0ba6579fbbca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("xliff_record", sa.Column("segment_id", sa.Integer()))
    # copy segment_id from id
    update = sa.update(sa.table("xliff_record", sa.Column("segment_id"))).values(
        segment_id=sa.column("id")
    )
    op.execute(update)
    # op.execute("UPDATE xliff_record SET segment_id = id")
    op.alter_column("xliff_record", "segment_id", nullable=False)


def downgrade() -> None:
    op.drop_column("xliff_record", "segment_id")

"""Make approved column for all types of records

Revision ID: 18b485855e40
Revises: 774a615d891f
Create Date: 2024-09-02 22:33:26.763402

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "18b485855e40"
down_revision: Union[str, None] = "774a615d891f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

dr = sa.table(
    "document_record",
    sa.column("id", sa.Integer()),
    sa.column("approved", sa.Boolean()),
)
xr = sa.table(
    "xliff_record",
    sa.column("parent_id", sa.Integer()),
    sa.column("approved", sa.Boolean()),
)


def upgrade() -> None:
    op.add_column("document_record", sa.Column("approved", sa.Boolean()))
    op.execute(sa.update(dr).values(approved=False))
    op.execute(
        sa.update(dr).values(approved=xr.c.approved).where(xr.c.parent_id == dr.c.id)
    )
    op.alter_column("document_record", "approved", nullable=False)
    op.drop_column("xliff_record", "approved")


def downgrade() -> None:
    op.add_column(
        "xliff_record",
        sa.Column("approved", sa.Boolean(), autoincrement=False),
    )
    op.execute(
        sa.update(xr).values(approved=dr.c.approved).where(dr.c.id == xr.c.parent_id)
    )
    op.alter_column("xliff_record", "approved", nullable=False)
    op.drop_column("document_record", "approved")

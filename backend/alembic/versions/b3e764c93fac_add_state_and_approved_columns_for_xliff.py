"""Add state and approved columns for xliff

Revision ID: b3e764c93fac
Revises: a61da93aeb2b
Create Date: 2024-07-09 23:09:22.098405

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "b3e764c93fac"
down_revision: Union[str, None] = "a61da93aeb2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("xliff_record", sa.Column("state", sa.String()))
    op.add_column("xliff_record", sa.Column("approved", sa.Boolean()))
    update = sa.update(
        sa.table("xliff_record", sa.column("state"), sa.column("approved"))
    ).values(state="needs-translation", approved=False)
    op.execute(update)
    op.alter_column("xliff_record", "state", nullable=False)
    op.alter_column("xliff_record", "approved", nullable=False)


def downgrade() -> None:
    op.drop_column("xliff_record", "approved")
    op.drop_column("xliff_record", "state")

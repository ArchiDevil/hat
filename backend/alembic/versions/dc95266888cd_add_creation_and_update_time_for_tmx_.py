"""Add creation and update time for tmx segments

Revision ID: dc95266888cd
Revises: 68219fe4ad46
Create Date: 2024-06-15 15:53:02.568867

"""

from datetime import datetime, UTC
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "dc95266888cd"
down_revision: Union[str, None] = "68219fe4ad46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tmx_record", sa.Column("creation_date", sa.DateTime()))
    op.add_column("tmx_record", sa.Column("change_date", sa.DateTime()))

    update = sa.update(
        sa.table("tmx_record", sa.column("creation_date"), sa.column("change_date")),
    ).values(
        creation_date=datetime.now(UTC),
        change_date=datetime.now(UTC),
    )
    op.execute(update)

    op.alter_column("tmx_record", "creation_date", nullable=False)
    op.alter_column("tmx_record", "change_date", nullable=False)


def downgrade() -> None:
    op.drop_column("tmx_record", "change_date")
    op.drop_column("tmx_record", "creation_date")

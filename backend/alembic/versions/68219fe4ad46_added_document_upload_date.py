"""Added document upload time

Revision ID: 68219fe4ad46
Revises: f83699ff2dd0
Create Date: 2024-05-04 22:48:56.749079

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "68219fe4ad46"
down_revision: Union[str, None] = "f83699ff2dd0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("xliff_document", sa.Column("upload_time", sa.DateTime()))

    update = sa.update(sa.table("xliff_document", sa.Column("upload_time"))).values(
        upload_time=sa.func.now()
    )
    op.execute(update)
    op.alter_column("xliff_document", "upload_time", nullable=False)


def downgrade() -> None:
    op.drop_column("xliff_document", "upload_time")

"""Add links between users and documents

Revision ID: a61da93aeb2b
Revises: 9356f0b5cdd9
Create Date: 2024-06-29 14:53:17.965879

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "a61da93aeb2b"
down_revision: Union[str, None] = "9356f0b5cdd9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TMX part
    op.add_column("tmx_document", sa.Column("created_by", sa.Integer()))
    update = sa.update(
        sa.table("tmx_document", sa.Column("created_by", sa.Integer()))
    ).values(
        created_by=1  # first administrator account
    )
    op.execute(update)
    op.alter_column("tmx_document", "created_by", nullable=False)
    op.create_foreign_key(
        "tmx_document_user_id_key", "tmx_document", "user", ["created_by"], ["id"]
    )

    # XLIFF part
    op.add_column("xliff_document", sa.Column("created_by", sa.Integer()))
    update = sa.update(
        sa.table("xliff_document", sa.Column("created_by", sa.Integer()))
    ).values(
        created_by=1  # first administrator account
    )
    op.execute(update)
    op.alter_column("xliff_document", "created_by", nullable=False)
    op.create_foreign_key(
        "xliff_document_user_id_key", "xliff_document", "user", ["created_by"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "xliff_document_user_id_key", "xliff_document", type_="foreignkey"
    )
    op.drop_column("xliff_document", "created_by")
    op.drop_constraint("tmx_document_user_id_key", "tmx_document", type_="foreignkey")
    op.drop_column("tmx_document", "created_by")

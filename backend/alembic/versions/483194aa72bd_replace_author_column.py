"""Replace author column

Revision ID: 483194aa72bd
Revises: 18b485855e40
Create Date: 2024-09-12 01:21:43.226155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '483194aa72bd'
down_revision: Union[str, None] = '18b485855e40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # update glossary record table
    op.add_column('glossary_record', sa.Column('created_by', sa.Integer()))
    op.create_foreign_key(None, 'glossary_record', 'user', ['created_by'], ['id'])
    op.execute(
        sa.update(sa.table("glossary_record", sa.Column("created_by"))).values(
            created_by=1  # first administrator account
        )
    )
    op.alter_column('glossary_record', 'created_by', nullable=False)
    op.drop_column('glossary_record', 'author')

    # update glossary table
    op.alter_column('glossary', 'user_id', new_column_name='created_by')
    op.drop_constraint('glossary_user_id_fkey', "glossary", type_="foreignkey")
    op.create_foreign_key(
        "glossary_created_by_fkey",
        "glossary",
        "user",
        ["created_by"],
        ["id"],
    )


def downgrade() -> None:
    op.alter_column('glossary', 'created_by', new_column_name='user_id')
    op.drop_constraint('glossary_created_by_fkey', "glossary", type_="foreignkey")
    op.create_foreign_key(
        "glossary_user_id_fkey",
        "glossary",
        "user",
        ["user_id"],
        ["id"],
    )

    op.add_column('glossary_record', sa.Column('author', sa.String(), autoincrement=False, nullable=True))
    op.drop_constraint('glossary_record_created_by_fkey', 'glossary_record', type_='foreignkey')
    op.drop_column('glossary_record', 'created_by')

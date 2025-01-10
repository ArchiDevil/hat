"""Add stemmed source column

Revision ID: 3249385a213d
Revises: 483194aa72bd
Create Date: 2025-01-06 01:30:20.510813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.linguistic.utils import stem_sentence


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '3249385a213d'
down_revision: Union[str, None] = '483194aa72bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('glossary_record', sa.Column('stemmed_source', sa.String(), nullable=True))

    # Create a session to interact with the database
    connection = op.get_bind()
    Session = sessionmaker(bind=connection)
    session = Session()

    table_desc = sa.table('glossary_record', sa.column('id'), sa.column('source'), sa.column('stemmed_source'))

    try:
        # Fetch all records from the glossary_record table
        query = sa.select(table_desc)
        result = session.execute(query).fetchall()

        # Apply the stem_sentence function to each record and update the database
        for row in result:
            stemmed_value = stem_sentence(row.source)
            update_stmt = sa.update(table_desc).where(table_desc.c.id == row.id).values(stemmed_source=' '.join(stemmed_value))
            session.execute(update_stmt)

        # Commit the transaction
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

    op.alter_column('glossary_record', 'stemmed_source', nullable=False)


def downgrade() -> None:
    op.drop_column('glossary_record', 'stemmed_source')

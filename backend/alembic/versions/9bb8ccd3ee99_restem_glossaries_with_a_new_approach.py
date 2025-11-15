"""Restem glossaries with a new approach

Revision ID: 9bb8ccd3ee99
Revises: 68fc022af7a6
Create Date: 2025-11-15 22:49:50.546891

"""

from typing import Sequence, Union

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.linguistic.utils import postprocess_stemmed_segment, stem_sentence


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "9bb8ccd3ee99"
down_revision: Union[str, None] = "68fc022af7a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        return

    # Create a session to interact with the database
    connection = op.get_bind()
    Session = sessionmaker(bind=connection)
    session = Session()

    table_desc = sa.table(
        "glossary_record",
        sa.column("id"),
        sa.column("source"),
        sa.column("stemmed_source"),
    )

    try:
        # Fetch all records from the glossary_record table
        query = sa.select(table_desc)
        result = session.execute(query).fetchall()

        # Apply the new stemming approach: postprocess_stemmed_segment(stem_sentence(source))
        for row in result:
            stemmed_value = postprocess_stemmed_segment(stem_sentence(row.source))
            update_stmt = (
                sa.update(table_desc)
                .where(table_desc.c.id == row.id)
                .values(stemmed_source=" ".join(stemmed_value))
            )
            session.execute(update_stmt)

        # Commit the transaction
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def downgrade() -> None:
    # Create a session to interact with the database
    connection = op.get_bind()
    Session = sessionmaker(bind=connection)
    session = Session()

    table_desc = sa.table(
        "glossary_record",
        sa.column("id"),
        sa.column("source"),
        sa.column("stemmed_source"),
    )

    try:
        # Fetch all records from the glossary_record table
        query = sa.select(table_desc)
        result = session.execute(query).fetchall()

        # Apply the old stemming approach: just stem_sentence
        for row in result:
            stemmed_value = stem_sentence(row.source)
            update_stmt = (
                sa.update(table_desc)
                .where(table_desc.c.id == row.id)
                .values(stemmed_source=" ".join(stemmed_value))
            )
            session.execute(update_stmt)

        # Commit the transaction
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

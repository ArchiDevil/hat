"""Convert DocumentRecordHistoryChangeType enum to string

Revision ID: dcd734dfe9c4
Revises: 71a5eef94341
Create Date: 2026-02-17 02:32:03.411573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'dcd734dfe9c4'
down_revision: Union[str, None] = '71a5eef94341'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

change_type_enum = sa.Enum(
    'initial_import',
    'machine_translation',
    'tm_substitution',
    'glossary_substitution',
    'repetition',
    'manual_edit',
    name='documentrecordhistorychangetype'
)


def upgrade() -> None:
    # Convert enum column to text/string for flexibility
    op.alter_column(
        'document_record_history',
        'change_type',
        type_=sa.Text(),
    )
    change_type_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    # Convert any translation_update values to manual_edit before recreating enum
    op.execute(
        sa.text("""
            UPDATE document_record_history
            SET change_type = 'manual_edit'
            WHERE change_type = 'translation_update';
        """)
    )

    # Recreate enum type (without translation_update)
    change_type_enum.create(op.get_bind(), checkfirst=True)

    # Convert text column back to enum
    op.execute(
        sa.text("""
            ALTER TABLE document_record_history
            ALTER COLUMN change_type TYPE documentrecordhistorychangetype
            USING change_type::text::documentrecordhistorychangetype;
        """)
    )

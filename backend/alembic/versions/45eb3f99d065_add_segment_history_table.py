"""Add segment history table

Revision ID: 45eb3f99d065
Revises: 4a5b6c7d8e9f
Create Date: 2026-01-18 14:29:20.969142

"""
from datetime import datetime, UTC
import json
from typing import Sequence, Union

from alembic import op, context
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '45eb3f99d065'
down_revision: Union[str, None] = '4a5b6c7d8e9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

change_type = sa.Enum(
    'initial_import',
    'machine_translation',
    'tm_substitution',
    'glossary_substitution',
    'repetition',
    'manual_edit',
    name='documentrecordhistorychangetype'
)


def upgrade() -> None:
    # change_type will be created automatically from create_table
    op.create_table(
        'document_record_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('diff', sa.String(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('change_type', change_type, nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['record_id'], ['document_record.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('document_record_history_record_id_idx', 'document_record_history', ['record_id'], unique=False)

    if not context.is_offline_mode():
        connection = op.get_bind()
        result = connection.execute(sa.text('SELECT id, target FROM document_record'))
        for record_id, target in result:
            diff = json.dumps({
                "ops": [[
                    "insert",
                    0,
                    0,
                    target
                ]],
                "old_len": 0
            })
            connection.execute(
                sa.text(
                    "INSERT INTO document_record_history (record_id, diff, author_id, timestamp, change_type) VALUES (:record_id, :diff, NULL, :timestamp, 'initial_import')",
                ),
                {
                    "record_id": record_id,
                    "diff": diff,
                    "timestamp": str(datetime.now(UTC)),
                }
            )


def downgrade() -> None:
    op.drop_index('document_record_history_record_id_idx', table_name='document_record_history')
    op.drop_table('document_record_history')
    change_type.drop(op.get_bind())

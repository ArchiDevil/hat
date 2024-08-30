"""Rename TMX to TranslationMemory

Revision ID: bc813d99ccfb
Revises: 182d14227dee
Create Date: 2024-08-11 17:16:38.567927

"""
from typing import Sequence, Union

from alembic import op

# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'bc813d99ccfb'
down_revision: Union[str, None] = '182d14227dee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('trgm_tmx_src_idx', table_name='tmx_record', postgresql_using='gist')
    op.rename_table('tmx_record', 'translation_memory_record')
    op.create_index(
        'trgm_tm_src_idx',
        'translation_memory_record',
        ['source'],
        postgresql_ops={'source': 'gist_trgm_ops'},
        unique=False,
        postgresql_using='gist'
    )
    op.rename_table('doc_to_tmx', 'document_to_translation_memory')
    op.drop_constraint('doc_to_tmx_tmx_id_fkey', 'document_to_translation_memory')
    op.alter_column('document_to_translation_memory', 'tmx_id', new_column_name='tm_id')
    op.drop_constraint('tmx_record_document_id_fkey', 'translation_memory_record')

    op.rename_table('tmx_document', 'translation_memory')
    op.create_foreign_key(
        'document_to_translation_memory_tm_id_fkey',
        'document_to_translation_memory',
        'translation_memory',
        ['tm_id'],
        ['id']
    )
    op.create_foreign_key(
        'translation_memory_record_document_id_fkey',
        'translation_memory_record',
        'translation_memory',
        ['document_id'],
        ['id']
    )


def downgrade() -> None:
    op.drop_constraint(
        'translation_memory_record_document_id_fkey',
        'translation_memory_record'
    )
    op.drop_constraint('document_to_translation_memory_tm_id_fkey', 'document_to_translation_memory')
    op.rename_table('translation_memory', 'tmx_document')

    op.create_foreign_key(
        'tmx_record_document_id_fkey',
        'translation_memory_record',
        'tmx_document',
        ['document_id'],
        ['id']
    )
    op.alter_column('document_to_translation_memory', 'tm_id', new_column_name='tmx_id')
    op.create_foreign_key(
        'doc_to_tmx_tmx_id_fkey',
        'document_to_translation_memory',
        'tmx_document',
        ['tmx_id'],
        ['id']
    )
    op.rename_table('document_to_translation_memory', 'doc_to_tmx')
    op.drop_index(
        'trgm_tm_src_idx',
        table_name='translation_memory_record',
        postgresql_using='gist'
    )
    op.rename_table('translation_memory_record', 'tmx_record')
    op.create_index(
        'trgm_tmx_src_idx',
        'tmx_record',
        ['source'],
        postgresql_ops={'source': 'gist_trgm_ops'},
        unique=False,
        postgresql_using='gist',
    )

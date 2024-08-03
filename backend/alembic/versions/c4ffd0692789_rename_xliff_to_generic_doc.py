"""Rename XLIFF to generic doc

Revision ID: c4ffd0692789
Revises: 5d15972f5415
Create Date: 2024-07-30 22:37:56.493442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'c4ffd0692789'
down_revision: Union[str, None] = '5d15972f5415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # drop constraints on all foreign keys to rename them
    op.drop_constraint('xliff_record_to_tmx_tmx_id_fkey', 'xliff_record_to_tmx')
    op.drop_constraint('xliff_record_to_tmx_xliff_id_fkey', 'xliff_record_to_tmx')
    op.drop_constraint('xliff_record_document_id_fkey', 'xliff_record')

    # rename tables
    op.rename_table('xliff_record_to_tmx', 'doc_to_tmx')
    op.rename_table('xliff_document', 'document')
    op.rename_table('xliff_record', 'document_record')

    # update table internals
    op.alter_column('doc_to_tmx', 'xliff_id', new_column_name='doc_id')

    # add foreign keys back to rename them
    op.create_foreign_key(None, 'doc_to_tmx', 'document', ['doc_id'], ['id'])
    op.create_foreign_key(None, 'doc_to_tmx', 'tmx_document', ['tmx_id'], ['id'])
    op.create_foreign_key(None, 'document_record', 'document', ['document_id'], ['id'])


def downgrade() -> None:
    # drop newly created foreign keys
    op.drop_constraint('doc_to_tmx_doc_id_fkey', 'doc_to_tmx')
    op.drop_constraint('doc_to_tmx_tmx_id_fkey', 'doc_to_tmx')
    op.drop_constraint('document_record_document_id_fkey', 'document_record')

    # rename table internals back to original name
    op.alter_column('doc_to_tmx', 'doc_id', new_column_name='xliff_id')

    # rename table back to original name
    op.rename_table('document_record', 'xliff_record')
    op.rename_table('document', 'xliff_document')
    op.rename_table('doc_to_tmx', 'xliff_record_to_tmx')

    # create foreign keys back
    op.create_foreign_key(None, 'xliff_record', 'xliff_document', ['document_id'], ['id'])
    op.create_foreign_key(None, 'xliff_record_to_tmx', 'xliff_document', ['xliff_id'], ['id'])
    op.create_foreign_key(None, 'xliff_record_to_tmx', 'tmx_document', ['tmx_id'], ['id'])

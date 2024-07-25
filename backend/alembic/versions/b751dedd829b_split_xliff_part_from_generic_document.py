"""Split XLIFF part from generic document

Revision ID: b751dedd829b
Revises: c4ffd0692789
Create Date: 2024-07-31 22:04:31.218013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = 'b751dedd829b'
down_revision: Union[str, None] = 'c4ffd0692789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # split xliff documents into separate table
    op.create_table('xliff_document',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('original_document', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['document.id']),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute('''
        INSERT INTO xliff_document (parent_id, original_document)
        SELECT d.id, d.original_document
        FROM document d
    ''')
    op.drop_column('document', 'original_document')

    # split xliff records into separate table
    op.create_table('xliff_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['document_record.id']),
        sa.ForeignKeyConstraint(['document_id'], ['xliff_document.id']),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute('''
        INSERT INTO xliff_record (parent_id, segment_id, document_id, state, approved)
        SELECT dr.id, dr.segment_id, xd.id, dr.state, dr.approved
        FROM document_record dr, xliff_document xd
        WHERE dr.document_id = xd.parent_id
    ''')
    op.drop_column('document_record', 'segment_id')
    op.drop_column('document_record', 'state')
    op.drop_column('document_record', 'approved')


def downgrade() -> None:
    op.add_column('document_record', sa.Column('approved', sa.Boolean()))
    op.add_column('document_record', sa.Column('state', sa.String()))
    op.add_column('document_record', sa.Column('segment_id', sa.Integer()))

    op.execute('''
        UPDATE document_record dr
        SET segment_id = xr.segment_id,
            state = xr.state,
            approved = xr.approved
        FROM xliff_record xr
        WHERE dr.id = xr.parent_id
    ''')
    op.alter_column('document_record','segment_id', nullable=False)
    op.alter_column('document_record','state', nullable=False)
    op.alter_column('document_record', 'approved', nullable=False)
    op.drop_table('xliff_record')

    op.add_column('document', sa.Column('original_document', sa.String(), nullable=True))
    op.execute('''
        UPDATE document d
        SET original_document = (
            SELECT xd.original_document
            FROM xliff_document xd
            WHERE xd.parent_id = d.id
            LIMIT 1
        )
    ''')
    op.alter_column('document', 'original_document', nullable=False)
    op.drop_table('xliff_document')

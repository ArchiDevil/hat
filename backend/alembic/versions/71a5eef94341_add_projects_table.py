"""Add projects table

Revision ID: 71a5eef94341
Revises: c12df3eda4a2
Create Date: 2026-01-25 21:09:10.356746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = '71a5eef94341'
down_revision: Union[str, None] = 'c12df3eda4a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('document', sa.Column('project_id', sa.Integer(), nullable=True))
    op.create_foreign_key('document_project_id_fkey', 'document', 'projects', ['project_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('document_project_id_fkey', 'document', type_='foreignkey')
    op.drop_column('document', 'project_id')
    op.drop_table('projects')

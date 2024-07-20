"""Add glossary

Revision ID: 6d107741a92e
Revises: b3e764c93fac
Create Date: 2024-07-17 01:01:34.146777

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

revision: str = "6d107741a92e"
down_revision: Union[str, None] = "b3e764c93fac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "glossary_document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "glossary_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["glossary_document.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("glossary_record")
    op.drop_table("glossary_document")

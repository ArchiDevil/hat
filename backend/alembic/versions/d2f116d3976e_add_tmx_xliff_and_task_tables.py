"""Add TMX, XLIFF and Task tables

Revision ID: d2f116d3976e
Revises: ab1574d1a1da
Create Date: 2023-12-07 00:56:49.742016

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# pylint: disable=E1101

# revision identifiers, used by Alembic.
revision: str = "d2f116d3976e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tmx_document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tmx_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=False),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("change_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["tmx_document.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "xliff_document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("original_document", sa.String(), nullable=False),
        sa.Column("processing_status", sa.String(), nullable=False),
        sa.Column("upload_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "xliff_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=False),
        sa.Column("segment_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["xliff_document.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "document_task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("document_task")

    op.drop_table("xliff_record")
    op.drop_table("xliff_document")

    op.drop_table("tmx_record")
    op.drop_table("tmx_document")

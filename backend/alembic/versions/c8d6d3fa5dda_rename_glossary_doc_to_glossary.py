"""rename_glossary_doc_to_glossary

Revision ID: c8d6d3fa5dda
Revises: 871e5285a2a3
Create Date: 2024-08-21 18:31:25.021590

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c8d6d3fa5dda"
down_revision: Union[str, None] = "871e5285a2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "glossary",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("processing_status", sa.String(), nullable=False),
        sa.Column("upload_time", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.drop_constraint(
        "glossary_record_document_id_fkey", "glossary_record", type_="foreignkey"
    )
    op.drop_table("glossary_document")
    op.add_column(
        "glossary_record", sa.Column("glossary_id", sa.Integer(), nullable=False)
    )

    op.create_foreign_key(None, "glossary_record", "glossary", ["glossary_id"], ["id"])
    op.drop_column("glossary_record", "document_id")


def downgrade() -> None:
    op.add_column(
        "glossary_record",
        sa.Column("document_id", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.drop_constraint("glossary_record_glossary_id_fkey", "glossary_record", type_="foreignkey")

    op.drop_column("glossary_record", "glossary_id")
    op.create_table(
        "glossary_document",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "processing_status", sa.VARCHAR(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "upload_time", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name="glossary_document_user_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="glossary_document_pkey"),
    )
    op.create_foreign_key(
        "glossary_record_document_id_fkey",
        "glossary_record",
        "glossary_document",
        ["document_id"],
        ["id"],
    )
    op.drop_table("glossary")

"""change_glossary_document_drop_unnecessary_fields

Revision ID: 5d15972f5415
Revises: 15355f38c714
Create Date: 2024-07-26 11:58:07.599004

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5d15972f5415"
down_revision: Union[str, None] = "15355f38c714"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "glossary_document", sa.Column("processing_status", sa.String(), nullable=False)
    )
    op.add_column(
        "glossary_document", sa.Column("upload_time", sa.DateTime(), nullable=False)
    )
    op.add_column(
        "glossary_document", sa.Column("user_id", sa.Integer(), nullable=False)
    )
    op.drop_constraint(
        "glossary_document_created_by_fkey", "glossary_document", type_="foreignkey"
    )
    op.create_foreign_key(None, "glossary_document", "user", ["user_id"], ["id"])
    op.drop_column("glossary_document", "created_by")
    op.add_column("glossary_record", sa.Column("author", sa.String(), nullable=False))
    op.alter_column(
        "glossary_record", "comment", existing_type=sa.VARCHAR(), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "glossary_record", "comment", existing_type=sa.VARCHAR(), nullable=False
    )
    op.drop_column("glossary_record", "author")
    op.add_column(
        "glossary_document",
        sa.Column("created_by", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(None, "glossary_document", type_="foreignkey")
    op.create_foreign_key(
        "glossary_document_created_by_fkey",
        "glossary_document",
        "user",
        ["created_by"],
        ["id"],
    )
    op.drop_column("glossary_document", "user_id")
    op.drop_column("glossary_document", "upload_time")
    op.drop_column("glossary_document", "processing_status")

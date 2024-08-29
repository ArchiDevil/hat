"""rename_glossary_doc_to_glossary

Revision ID: c8d6d3fa5dda
Revises: 871e5285a2a3
Create Date: 2024-08-21 18:31:25.021590

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# pylint: disable=E1101

revision: str = "c8d6d3fa5dda"
down_revision: Union[str, None] = "871e5285a2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


gt = sa.table(
    'glossary',
    sa.column('id'),
    sa.column('created_at'),
    sa.column('updated_at'),
    sa.column('name'),
    sa.column('processing_status'),
    sa.column('upload_time'),
    sa.column('user_id'),
)

gdt = sa.table(
    'glossary_document',
    sa.column('id'),
    sa.column('created_at'),
    sa.column('updated_at'),
    sa.column('name'),
    sa.column('processing_status'),
    sa.column('upload_time'),
    sa.column('user_id'),
)

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

    insert = sa.insert(gt).from_select(
        [
            'id', 'created_at', 'updated_at', 'name',
            'processing_status', 'upload_time', 'user_id'
        ],
        sa.select(
            gdt.c.id, gdt.c.created_at, gdt.c.updated_at, gdt.c.name,
            gdt.c.processing_status, gdt.c.upload_time, gdt.c.user_id
        )
    )
    op.execute(insert)
    op.drop_constraint(
        "glossary_record_document_id_fkey", "glossary_record", type_="foreignkey"
    )
    op.drop_table("glossary_document")
    op.add_column(
        "glossary_record", sa.Column("glossary_id", sa.Integer())
    )
    op.execute(
        sa.update(
            sa.table(
                "glossary_record",
                sa.column('glossary_id'),
                sa.column('document_id')
            )
        ).values(glossary_id=sa.column('document_id'))
    )
    op.alter_column('glossary_record', 'glossary_id', nullable=False)

    op.create_foreign_key(None, "glossary_record", "glossary", ["glossary_id"], ["id"])
    op.drop_column("glossary_record", "document_id")


def downgrade() -> None:
    op.add_column(
        "glossary_record",
        sa.Column("document_id", sa.Integer(), autoincrement=False),
    )
    op.execute(
        sa.update(
            sa.table("glossary_record",
                     sa.column('glossary_id'),
                     sa.column('document_id')
                    )
            ).values(document_id=sa.column('glossary_id')))
    op.alter_column('glossary_record', 'document_id', nullable=False)
    op.drop_constraint("glossary_record_glossary_id_fkey", "glossary_record", type_="foreignkey")

    op.drop_column("glossary_record", "glossary_id")
    op.create_table(
        "glossary_document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "processing_status", sa.String(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "upload_time", sa.DateTime(), autoincrement=False, nullable=False
        ),
        sa.Column("user_id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("name", sa.String(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name="glossary_document_user_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="glossary_document_pkey"),
    )
    insert = sa.insert(gdt).from_select(
        [
            'id', 'created_at', 'updated_at', 'name',
            'processing_status', 'upload_time', 'user_id'
        ],
        sa.select(
            gt.c.id, gt.c.created_at, gt.c.updated_at, gt.c.name,
            gt.c.processing_status, gt.c.upload_time, gt.c.user_id
        )
    )
    op.execute(insert)
    op.create_foreign_key(
        "glossary_record_document_id_fkey",
        "glossary_record",
        "glossary_document",
        ["document_id"],
        ["id"],
    )
    op.drop_table("glossary")

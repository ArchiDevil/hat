from dataclasses import dataclass
from typing import Optional, Self

from sqlalchemy.orm import Session

from app.glossary.models import GlossaryRecord
from app.glossary.query import (
    bulk_create_glossary_record,
    update_glossary_doc_processing_status,
)


@dataclass
class GlossaryRowRecord:
    comment: Optional[str]
    created_at: str
    author: str
    updated_at: str
    source: str
    target: str

    @classmethod
    def from_tuple(cls, data_tuple: tuple[str, ...]) -> Self:
        comment, created_at, author, updated_at, _, source, target = data_tuple
        return cls(comment, created_at, author, updated_at, source, target)


def create_glossary_doc_from_file_tasks(sheet, db: Session, glossary_doc_id: int):
    record_for_save = []
    for index, cells in enumerate(sheet.iter_rows()):
        if index > 0:
            parsed_record = GlossaryRowRecord.from_tuple(
                tuple(cell.value for cell in cells)
            )
            record = GlossaryRecord(
                author=parsed_record.author,
                created_at=parsed_record.created_at,
                updated_at=parsed_record.updated_at,
                comment=parsed_record.comment,
                source=parsed_record.source,
                target=parsed_record.target,
                document_id=glossary_doc_id,
            )
            record_for_save.append(record)
    bulk_create_glossary_record(db, record_for_save)
    update_glossary_doc_processing_status(db, doc_id=glossary_doc_id)

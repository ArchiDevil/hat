from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self

from sqlalchemy.orm import Session

from app.glossary.models import GlossaryRecord
from app.glossary.query import GlossaryDocsQuery


@dataclass
class GlossaryRowRecord:
    comment: Optional[str]
    created_at: datetime
    author: str
    updated_at: datetime
    source: str
    target: str

    @classmethod
    def from_tuple(cls, data_tuple: tuple[str, ...]) -> Self:
        comment, created_at, author, updated_at, _, source, target = data_tuple
        created_at = datetime.strptime(created_at, "%m/%d/%Y %H:%M:%S")
        updated_at = datetime.strptime(updated_at, "%m/%d/%Y %H:%M:%S")
        return cls(comment, created_at, author, updated_at, source, target)


def create_glossary_doc_from_file_tasks(sheet, db: Session, glossary_doc_id: int):
    record_for_save = extract_from_xlsx(sheet, glossary_doc_id)
    bulk_save_doc_update_processing_status(
        db=db, record_for_save=record_for_save, glossary_doc_id=glossary_doc_id
    )


def extract_from_xlsx(sheet, glossary_doc_id) -> list[GlossaryRecord]:
    record_for_save = []
    for cells in sheet.iter_rows(min_row=2, values_only=True):
        parsed_record = GlossaryRowRecord.from_tuple(cells)
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
    return record_for_save


def bulk_save_doc_update_processing_status(
    db: Session, record_for_save: list[GlossaryRecord], glossary_doc_id: int
):
    glossary_doc_query = GlossaryDocsQuery(db)
    glossary_doc_query.bulk_create_glossary_record(record_for_save)
    glossary_doc_query.update_glossary_doc_processing_status(glossary_doc_id)

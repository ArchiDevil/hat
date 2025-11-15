from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self

from sqlalchemy.orm import Session

from app.glossary.models import GlossaryRecord
from app.glossary.query import GlossaryQuery
from app.linguistic.utils import postprocess_stemmed_segment, stem_sentence


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


def create_glossary_from_file_tasks(user_id: int, sheet, db: Session, glossary_id: int):
    record_for_save = extract_from_xlsx(user_id, sheet, glossary_id)
    bulk_save_glossaries_update_processing_status(
        db=db, record_for_save=record_for_save, glossary_id=glossary_id
    )


def extract_from_xlsx(user_id: int, sheet, glossary_id: int) -> list[GlossaryRecord]:
    record_for_save = []
    for cells in sheet.iter_rows(min_row=2, values_only=True):
        parsed_record = GlossaryRowRecord.from_tuple(cells)
        record = GlossaryRecord(
            created_by=user_id,
            created_at=parsed_record.created_at,
            updated_at=parsed_record.updated_at,
            comment=parsed_record.comment,
            source=parsed_record.source,
            target=parsed_record.target,
            glossary_id=glossary_id,
            stemmed_source=" ".join(
                postprocess_stemmed_segment(stem_sentence(parsed_record.source))
            ),
        )
        record_for_save.append(record)
    return record_for_save


def bulk_save_glossaries_update_processing_status(
    db: Session, record_for_save: list[GlossaryRecord], glossary_id: int
):
    glossary_query = GlossaryQuery(db)
    glossary_query.bulk_create_glossary_record(record_for_save)
    glossary_query.update_glossary_processing_status(glossary_id)

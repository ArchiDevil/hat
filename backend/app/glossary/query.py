from typing import Type

from sqlalchemy.orm import Session

from app import GlossaryDocument, GlossaryRecord
from app.glossary.models import ProcessingStatuses


def create_glossary_doc(
    db: Session, document_name: str, user_id: int
) -> GlossaryDocument:
    glossary_doc = GlossaryDocument(
        original_document=document_name,
        user_id=user_id,
    )
    db.add(glossary_doc)
    db.commit()
    return glossary_doc


def update_glossary_doc_processing_status(
    db: Session, doc_id: int
) -> Type[GlossaryDocument] | None:
    doc = db.query(GlossaryDocument).filter(GlossaryDocument.id == doc_id).first()
    if doc:
        doc.processing_status = ProcessingStatuses.DONE
        db.commit()
        return doc
    return None


def bulk_create_glossary_record(db: Session, records: list[GlossaryRecord]):
    db.add_all(records)
    db.commit()

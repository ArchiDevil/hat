from typing import Type

from sqlalchemy.orm import Session

from app import GlossaryDocument, GlossaryRecord
from app.glossary.models import ProcessingStatuses


class GlossaryDocsQuery:
    """Contain query to GlossaryDocument"""

    def __init__(self, db: Session):
        self.db = db

    def list_glossary_docs(self) -> list[Type[GlossaryDocument]]:
        return self.db.query(GlossaryDocument).order_by(GlossaryDocument.id).all()

    def create_glossary_doc(self, user_id: int) -> GlossaryDocument:
        glossary_doc = GlossaryDocument(
            user_id=user_id,
        )
        self.db.add(glossary_doc)
        self.db.commit()
        return glossary_doc

    def update_glossary_doc_processing_status(
        self, doc_id: int
    ) -> Type[GlossaryDocument] | None:
        doc = (
            self.db.query(GlossaryDocument)
            .filter(GlossaryDocument.id == doc_id)
            .first()
        )
        if doc:
            doc.processing_status = ProcessingStatuses.DONE
            self.db.commit()
            return doc
        return None

    def bulk_create_glossary_record(self, records: list[GlossaryRecord]):
        self.db.add_all(records)
        self.db.commit()

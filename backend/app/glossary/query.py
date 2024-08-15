from typing import Type

from sqlalchemy.orm import Session

from app import GlossaryDocument, GlossaryRecord
from app.base.exceptions import BaseQueryException
from app.glossary.models import ProcessingStatuses


class NotFoundGlossaryDocExc(BaseQueryException):
    """Not found glossary doc"""


class GlossaryQuery:
    """Contain query to GlossaryDocument"""

    def __init__(self, db: Session):
        self.db = db

    def get_glossary_doc(self, glossary_id: int) -> Type[GlossaryDocument]:
        doc = (
            self.db.query(GlossaryDocument)
            .filter(GlossaryDocument.id == glossary_id)
            .first()
        )
        if doc:
            return doc
        raise NotFoundGlossaryDocExc()

    def list_glossary_docs(self) -> list[Type[GlossaryDocument]]:
        return self.db.query(GlossaryDocument).order_by(GlossaryDocument.id).all()

    def list_glossary_records(
        self, document_id: int | None = None
    ) -> list[Type[GlossaryDocument]]:
        if document_id:
            return (
                self.db.query(GlossaryRecord)
                .filter(GlossaryRecord.document_id == document_id)
                .order_by(GlossaryRecord.id)
                .all()
            )
        return self.db.query(GlossaryRecord).order_by(GlossaryRecord.id).all()

    def create_glossary_doc(self, user_id: int, document_name: str) -> GlossaryDocument:
        glossary_doc = GlossaryDocument(
            user_id=user_id,
            name=document_name,
        )
        self.db.add(glossary_doc)
        self.db.commit()
        return glossary_doc

    def create_glossary_record(
        self,
        author: str,
        source: str,
        target: str,
        document_id: int,
        comment: str | None = None,
    ) -> GlossaryRecord:
        glossary_record = GlossaryRecord(
            author=author,
            comment=comment,
            source=source,
            target=target,
            document_id=document_id,
        )
        self.db.add(glossary_record)
        self.db.commit()
        return glossary_record

    def update_doc(
        self, document_id: int, document: GlossaryDocument
    ) -> Type[GlossaryDocument]:
        result = (
            self.db.query(GlossaryDocument)
            .filter(GlossaryDocument.id == document_id)
            .update(document.model_dump())
        )
        if result:
            self.db.commit()
            return self.get_glossary_doc(document_id)
        raise NotFoundGlossaryDocExc()

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

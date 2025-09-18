from datetime import datetime
from typing import Iterable

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.base.exceptions import BaseQueryException
from app.documents.schema import DocumentRecordUpdate
from app.glossary.models import Glossary
from app.models import DocumentStatus
from app.translation_memory.models import TranslationMemory
from app.translation_memory.query import TranslationMemoryQuery

from .models import (
    DocGlossaryAssociation,
    DocMemoryAssociation,
    Document,
    DocumentRecord,
    DocumentType,
    TmMode,
    TxtDocument,
    XliffDocument,
)


class NotFoundDocumentRecordExc(BaseQueryException):
    """Exception raised when document record not found"""


class GenericDocsQuery:
    """Contain query to Document"""

    def __init__(self, db: Session) -> None:
        self.__db = db

    def get_document(self, document_id: int) -> Document | None:
        return self.__db.execute(
            select(Document).filter(Document.id == document_id)
        ).scalar_one_or_none()

    def get_documents_list(self) -> Iterable[Document]:
        return self.__db.execute(
            select(Document)
            .filter(Document.processing_status != "uploaded")
            .order_by(Document.id)
        ).scalars()

    def get_outdated_documents(self, cutoff_date: datetime) -> Iterable[Document]:
        return self.__db.execute(
            select(Document)
            .filter(Document.upload_time < cutoff_date)
            .filter(Document.processing_status == "uploaded")
        ).scalars()

    def delete_document(self, document: Document):
        self.__db.delete(document)
        self.__db.commit()

    def bulk_delete_documents(self, documents: Iterable[Document]):
        for document in documents:
            self.__db.delete(document)
        self.__db.commit()

    def add_document(self, document: Document, original_document: str):
        self.__db.add(document)
        self.__db.commit()

        args = {"parent_id": document.id, "original_document": original_document}

        if document.type == DocumentType.xliff:
            self.__db.add(XliffDocument(**args))
        elif document.type == DocumentType.txt:
            self.__db.add(TxtDocument(**args))
        self.__db.commit()

    def enqueue_document(self, document: Document):
        document.processing_status = DocumentStatus.PENDING.value
        self.__db.commit()

    def get_document_records_count(self, doc: Document) -> tuple[int, int]:
        stmt = (
            select(
                func.count(case((DocumentRecord.approved.is_(True), 1))),
                func.count(),
            )
            .select_from(DocumentRecord)
            .where(DocumentRecord.document_id == doc.id)
        )
        result = self.__db.execute(stmt).one()
        return result[0], result[1]

    def get_document_records_paged(
        self, doc: Document, page: int, page_records=100
    ) -> Iterable[DocumentRecord]:
        return self.__db.execute(
            select(DocumentRecord)
            .filter(DocumentRecord.document_id == doc.id)
            .order_by(DocumentRecord.id)
            .offset(page_records * page)
            .limit(page_records)
        ).scalars()

    def get_record(self, record_id: int) -> DocumentRecord | None:
        return self.__db.execute(
            select(DocumentRecord).filter(DocumentRecord.id == record_id)
        ).scalar_one_or_none()

    def update_record(
        self, record_id: int, data: DocumentRecordUpdate
    ) -> DocumentRecord:
        record = self.get_record(record_id)
        if not record:
            raise NotFoundDocumentRecordExc()

        record.target = data.target
        if data.approved is not None:
            record.approved = data.approved

            if data.approved is True:
                bound_tm = None
                for memory in record.document.memory_associations:
                    if memory.mode == TmMode.write:
                        bound_tm = memory.tm_id

                if bound_tm:
                    TranslationMemoryQuery(self.__db).add_or_update_record(
                        bound_tm, record.source, record.target
                    )

        self.__db.commit()
        return record

    def set_document_memories(
        self, document: Document, memories: list[tuple[TranslationMemory, TmMode]]
    ):
        associations = [
            DocMemoryAssociation(document=document, memory=memory[0], mode=memory[1])
            for memory in memories
        ]
        document.memory_associations = associations
        self.__db.commit()

    def set_document_glossaries(self, document: Document, glossaries: list[Glossary]):
        associations = [
            DocGlossaryAssociation(document=document, glossary=glossary)
            for glossary in glossaries
        ]
        document.glossary_associations = associations
        self.__db.commit()

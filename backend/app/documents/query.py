from datetime import datetime
from typing import Iterable

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.documents.schema import DocumentRecordUpdate
from app.models import DocumentStatus
from app.translation_memory.models import TranslationMemory

from .models import (
    DocMemoryAssociation,
    Document,
    DocumentRecord,
    DocumentType,
    TmMode,
    TxtDocument,
    XliffDocument,
)


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

        if document.type == DocumentType.xliff:
            xliff_doc = XliffDocument(
                parent_id=document.id, original_document=original_document
            )
            self.__db.add(xliff_doc)
        elif document.type == DocumentType.txt:
            txt_doc = TxtDocument(
                parent_id=document.id, original_document=original_document
            )
            self.__db.add(txt_doc)

        self.__db.commit()

    def enqueue_document(
        self, document: Document, memories: Iterable[TranslationMemory]
    ):
        document.processing_status = DocumentStatus.PENDING.value
        self.__db.add_all(
            [
                DocMemoryAssociation(doc_id=document.id, tm_id=memory.id, mode="read")
                for memory in memories
            ]
        )
        self.__db.commit()

    def get_document_records_count(self, doc: Document) -> int:
        return self.__db.execute(
            select(func.count())
            .select_from(DocumentRecord)
            .filter(DocumentRecord.document_id == doc.id)
        ).scalar_one()

    def get_document_approved_records_count(self, doc: Document) -> int:
        return self.__db.execute(
            select(func.count())
            .select_from(DocumentRecord)
            .filter(DocumentRecord.document_id == doc.id)
            .filter(DocumentRecord.approved.is_(True))
        ).scalar_one()

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

    def update_record(self, record_id: int, data: DocumentRecordUpdate):
        values = {k: v for k, v in data.model_dump().items() if v}
        if not values:
            return True

        if not self.__db.execute(
            select(DocumentRecord).filter(DocumentRecord.id == record_id)
        ).scalar_one_or_none():
            return False

        self.__db.execute(
            update(DocumentRecord).values(values).where(DocumentRecord.id == record_id)
        )
        self.__db.commit()
        return True

    def set_document_memories(
        self, document: Document, memories: list[tuple[TranslationMemory, TmMode]]
    ):
        associations = [
            DocMemoryAssociation(document=document, memory=memory[0], mode=memory[1])
            for memory in memories
        ]
        document.memory_associations = associations
        self.__db.commit()

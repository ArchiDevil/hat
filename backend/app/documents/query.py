from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentStatus
from app.translation_memory.models import TranslationMemory

from .models import Document, DocumentRecord, DocumentType, TxtDocument, XliffDocument


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

    def enqueue_document(self, document: Document, tmx_file_ids: list[int]):
        document.processing_status = DocumentStatus.PENDING.value
        document.tms = list(
            self.__db.execute(
                select(TranslationMemory).filter(TranslationMemory.id.in_(tmx_file_ids))
            ).scalars()
        )
        self.__db.commit()

    def get_document_records(self, doc: Document) -> Iterable[DocumentRecord]:
        return self.__db.execute(
            select(DocumentRecord)
            .filter(DocumentRecord.document_id == doc.id)
            .order_by(DocumentRecord.id)
        ).scalars()

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

    def get_record(self, doc_id: int, record_id: int) -> DocumentRecord | None:
        return self.__db.execute(
            select(DocumentRecord).filter(
                DocumentRecord.id == record_id, DocumentRecord.document_id == doc_id
            )
        ).scalar_one_or_none()

    def update_record_target(self, record: DocumentRecord, target: str):
        record.target = target
        self.__db.commit()

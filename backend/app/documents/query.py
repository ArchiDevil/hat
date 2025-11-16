from datetime import datetime
from typing import Iterable

from sqlalchemy import Row, and_, case, func, select
from sqlalchemy.orm import Session

from app.base.exceptions import BaseQueryException
from app.documents.schema import DocumentRecordFilter, DocumentRecordUpdate
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

    def get_document_records_count_with_approved(
        self, doc: Document
    ) -> tuple[int, int]:
        stmt = select(
            func.count(case((DocumentRecord.approved.is_(True), 1))),
            func.count(DocumentRecord.id),
        ).where(DocumentRecord.document_id == doc.id)
        result = self.__db.execute(stmt).one()
        return result[0], result[1]

    def get_document_records_count_filtered(
        self, doc: Document, filters: DocumentRecordFilter | None = None
    ) -> int:
        base_query = select(func.count(DocumentRecord.id)).filter(
            DocumentRecord.document_id == doc.id
        )

        filter_conditions = []
        if filters:
            if filters.source_filter:
                filter_conditions.append(
                    DocumentRecord.source.ilike(f"%{filters.source_filter}%")
                )

            if filters.target_filter:
                filter_conditions.append(
                    DocumentRecord.target.ilike(f"%{filters.target_filter}%")
                )

            if filter_conditions:
                base_query = base_query.filter(and_(*filter_conditions))

        return self.__db.execute(base_query).scalar_one()

    def get_document_records_paged(
        self,
        doc: Document,
        page: int,
        page_records=100,
        filters: DocumentRecordFilter | None = None,
    ) -> Iterable[Row[tuple[DocumentRecord, int]]]:
        # Subquery to count repetitions for each source text within the document
        repetitions_subquery = (
            select(
                DocumentRecord.source,
                func.count(DocumentRecord.id).label("repetitions_count"),
            )
            .filter(DocumentRecord.document_id == doc.id)
            .group_by(DocumentRecord.source)
            .subquery()
        )

        # Build the base query
        query = (
            select(
                DocumentRecord,
                func.coalesce(repetitions_subquery.c.repetitions_count, 0).label(
                    "repetitions_count"
                ),
            )
            .filter(DocumentRecord.document_id == doc.id)
            .outerjoin(
                repetitions_subquery,
                DocumentRecord.source == repetitions_subquery.c.source,
            )
        )

        # Apply filters if provided
        if filters:
            filter_conditions = []

            if filters.source_filter:
                filter_conditions.append(
                    DocumentRecord.source.ilike(f"%{filters.source_filter}%")
                )

            if filters.target_filter:
                filter_conditions.append(
                    DocumentRecord.target.ilike(f"%{filters.target_filter}%")
                )

            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

        return self.__db.execute(
            query.order_by(DocumentRecord.id)
            .offset(page_records * page)
            .limit(page_records)
        ).all()

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

        # If update_repetitions is True AND the segment is being approved, find all records with the same source
        if data.update_repetitions and data.approved is True:
            repeated_records = (
                self.__db.execute(
                    select(DocumentRecord).filter(
                        DocumentRecord.document_id == record.document_id,
                        DocumentRecord.source == record.source,
                    )
                )
                .scalars()
                .all()
            )

            # Update all repeated records
            for repeated_record in repeated_records:
                repeated_record.target = data.target
                repeated_record.approved = data.approved

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

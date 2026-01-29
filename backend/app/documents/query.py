from datetime import datetime
from typing import Iterable

from sqlalchemy import Row, and_, case, func, select
from sqlalchemy.orm import Session

from app.base.exceptions import BaseQueryException
from app.comments.models import Comment
from app.documents.models import DocumentRecordHistory, DocumentRecordHistoryChangeType
from app.documents.schema import DocumentRecordFilter
from app.glossary.models import Glossary
from app.models import DocumentStatus
from app.translation_memory.models import TranslationMemory

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


class NotFoundDocumentExc(BaseQueryException):
    """Exception raised when document not found"""


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

    def get_document_word_count_with_approved(self, doc: Document) -> tuple[int, int]:
        """
        Returns tuple of (approved_word_count, total_word_count) for a document.
        """
        stmt = select(
            func.sum(
                case(
                    (DocumentRecord.approved.is_(True), DocumentRecord.word_count),
                    else_=0,
                )
            ),
            func.sum(DocumentRecord.word_count),
        ).where(DocumentRecord.document_id == doc.id)
        result = self.__db.execute(stmt).one()
        return result[0] or 0, result[1] or 0

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
    ) -> Iterable[Row[tuple[DocumentRecord, int, bool]]]:
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

        # Subquery to count comments for each document record
        comments_subquery = (
            select(
                Comment.record_id,
                func.count(Comment.id).label("comments_count"),
            )
            .group_by(Comment.record_id)
            .subquery()
        )

        # Build the base query
        query = (
            select(
                DocumentRecord,
                func.coalesce(repetitions_subquery.c.repetitions_count, 0).label(
                    "repetitions_count"
                ),
                case(
                    (func.coalesce(comments_subquery.c.comments_count, 0) > 0, True),
                    else_=False,
                ).label("has_comments"),
            )
            .filter(DocumentRecord.document_id == doc.id)
            .outerjoin(
                repetitions_subquery,
                DocumentRecord.source == repetitions_subquery.c.source,
            )
            .outerjoin(
                comments_subquery,
                DocumentRecord.id == comments_subquery.c.record_id,
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

    def update_document(
        self, doc_id: int, name: str | None, project_id: int | None
    ) -> Document:
        document = self.get_document(doc_id)
        if not document:
            raise NotFoundDocumentExc()

        if name is not None:
            document.name = name
        if project_id is not None:
            document.project_id = project_id if project_id != -1 else None
        self.__db.commit()
        self.__db.refresh(document)
        return document

    def get_record_ids_by_source(self, doc_id: int, source: str) -> list[int]:
        return list(
            self.__db.execute(
                select(DocumentRecord.id).where(
                    DocumentRecord.document_id == doc_id,
                    DocumentRecord.source == source,
                )
            )
            .scalars()
            .all()
        )

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


class DocumentRecordHistoryQuery:
    """Query class for segment history operations."""

    def __init__(self, db: Session) -> None:
        self.__db = db

    def get_history_by_record_id(
        self, record_id: int
    ) -> Iterable[DocumentRecordHistory]:
        return (
            self.__db.execute(
                select(DocumentRecordHistory)
                .filter(DocumentRecordHistory.record_id == record_id)
                .order_by(DocumentRecordHistory.timestamp.desc())
            )
            .scalars()
            .all()
        )

    def get_last_history_by_record_id(
        self, record_id: int
    ) -> DocumentRecordHistory | None:
        return self.__db.execute(
            select(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == record_id)
            .order_by(DocumentRecordHistory.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

    def create_history_entry(
        self,
        record_id: int,
        diff: str,
        author_id: int | None,
        change_type: DocumentRecordHistoryChangeType,
    ) -> DocumentRecordHistory:
        history = DocumentRecordHistory(
            record_id=record_id,
            diff=diff,
            author_id=author_id,
            change_type=change_type,
        )
        self.__db.add(history)
        self.__db.commit()
        return history

    def bulk_create_history_entry(
        self,
        record_id_to_diff: list[tuple[int, str]],
        author_id: int | None,
        change_type: DocumentRecordHistoryChangeType,
    ):
        histories = [
            DocumentRecordHistory(
                record_id=history[0],
                diff=history[1],
                author_id=author_id,
                change_type=change_type,
            )
            for history in record_id_to_diff
        ]
        self.__db.add_all(histories)
        self.__db.commit()

    def update_history_entry(
        self, history: DocumentRecordHistory, diff: str, timestamp: datetime
    ) -> DocumentRecordHistory:
        history.diff = diff
        history.timestamp = timestamp
        self.__db.commit()
        return history

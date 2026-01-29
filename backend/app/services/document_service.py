"""Document service for document and document record operations."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schema
from app.base.exceptions import BusinessLogicError, EntityNotFound
from app.comments.query import CommentsQuery
from app.comments.schema import CommentCreate, CommentResponse
from app.documents import schema as doc_schema
from app.documents.models import (
    Document,
    DocumentRecordHistory,
    DocumentRecordHistoryChangeType,
    DocumentType,
    TmMode,
    XliffRecord,
)
from app.documents.query import (
    DocumentRecordHistoryQuery,
    GenericDocsQuery,
    NotFoundDocumentRecordExc,
)
from app.documents.utils import compute_diff, reconstruct_from_diffs
from app.formats.txt import extract_txt_content
from app.formats.xliff import SegmentState, extract_xliff_content
from app.glossary.query import GlossaryQuery, NotFoundGlossaryExc
from app.glossary.schema import GlossaryRecordSchema, GlossaryResponse
from app.translation_memory.query import TranslationMemoryQuery
from app.translation_memory.schema import (
    MemorySubstitution,
    TranslationMemory,
    TranslationMemoryListResponse,
    TranslationMemoryListSimilarResponse,
)


@dataclass
class DownloadMemoryData:
    """Data for downloading translation memory as TMX file."""

    content: StreamingResponse
    filename: str


class DocumentService:
    """Service for document and document record operations."""

    def __init__(self, db: Session):
        self.__db = db
        self.__query = GenericDocsQuery(db)
        self.__comments_query = CommentsQuery(db)
        self.__glossary_query = GlossaryQuery(db)
        self.__tm_query = TranslationMemoryQuery(db)
        self.__history_query = DocumentRecordHistoryQuery(db)

    def get_documents(self) -> list[doc_schema.DocumentWithRecordsCount]:
        """
        Get list of all documents.

        Returns:
            List of DocumentWithRecordsCount objects
        """
        docs = self.__query.get_documents_list()
        output = []
        for doc in docs:
            records = self.__query.get_document_records_count_with_approved(doc)
            words = self.__query.get_document_word_count_with_approved(doc)
            output.append(
                doc_schema.DocumentWithRecordsCount(
                    id=doc.id,
                    name=doc.name,
                    status=models.DocumentStatus(doc.processing_status),
                    created_by=doc.created_by,
                    type=doc.type.value,
                    approved_records_count=records[0],
                    records_count=records[1],
                    approved_word_count=words[0],
                    total_word_count=words[1],
                )
            )
        return output

    def get_document(self, doc_id: int) -> doc_schema.DocumentWithRecordsCount:
        """
        Get a single document by ID.

        Args:
            doc_id: Document ID

        Returns:
            DocumentWithRecordsCount object

        Raises:
            EntityNotFound: If document not found
        """
        doc = self.__query.get_document(doc_id)
        if not doc:
            raise EntityNotFound("Document not found")
        records = self.__query.get_document_records_count_with_approved(doc)
        words = self.__query.get_document_word_count_with_approved(doc)
        return doc_schema.DocumentWithRecordsCount(
            id=doc.id,
            name=doc.name,
            status=models.DocumentStatus(doc.processing_status),
            created_by=doc.created_by,
            type=doc.type.value,
            approved_records_count=records[0],
            records_count=records[1],
            approved_word_count=words[0],
            total_word_count=words[1],
        )

    async def create_document(
        self, file: UploadFile, user_id: int
    ) -> doc_schema.Document:
        """
        Create a new document from uploaded file.

        Args:
            file: Uploaded file
            user_id: ID of user creating the document

        Returns:
            Created Document object

        Raises:
            EntityNotFound: If file type is unsupported
        """
        cutoff_date = datetime.now() - timedelta(days=1)

        # Remove outdated files when adding a new one
        outdated_docs = self.__query.get_outdated_documents(cutoff_date)
        self.__query.bulk_delete_documents(outdated_docs)

        name = str(file.filename)
        file_data = await file.read()
        original_document = file_data.decode("utf-8")

        # quite simple logic, but it is fine for now
        ext = name.lower().split(".")[-1]
        if ext == "xliff":
            doc_type = DocumentType.xliff
        elif ext == "txt":
            doc_type = DocumentType.txt
        else:
            raise BusinessLogicError("Unsupported file type")

        doc = Document(
            name=name,
            type=doc_type,
            processing_status=models.DocumentStatus.UPLOADED.value,
            upload_time=datetime.now(),
            created_by=user_id,
        )
        self.__query.add_document(doc, original_document)
        return doc_schema.Document(
            id=doc.id,
            name=doc.name,
            status=models.DocumentStatus(doc.processing_status),
            created_by=doc.created_by,
            type=doc.type.value,
        )

    def delete_document(self, doc_id: int) -> models.StatusMessage:
        """
        Delete a document.

        Args:
            doc_id: Document ID

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If document not found
        """
        doc = self._get_document_by_id(doc_id)
        self.__query.delete_document(doc)
        return models.StatusMessage(message="Deleted")

    def process_document(
        self, doc_id: int, settings: doc_schema.DocumentProcessingSettings
    ) -> models.StatusMessage:
        """
        Process a document.

        Args:
            doc_id: Document ID
            settings: Processing settings

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If document not found
        """
        doc = self._get_document_by_id(doc_id)
        self.__query.enqueue_document(doc)

        task_config = doc_schema.DocumentTaskDescription(
            type=doc.type.value, document_id=doc_id, settings=settings
        )
        self.__db.add(
            schema.DocumentTask(
                data=task_config.model_dump_json(),
                status=models.TaskStatus.PENDING.value,
            )
        )
        self.__db.commit()
        return models.StatusMessage(message="Ok")

    def download_document(self, doc_id: int) -> StreamingResponse:
        """
        Download a document.

        Args:
            doc_id: Document ID

        Returns:
            StreamingResponse with document file

        Raises:
            EntityNotFound: If document not found or file not available
        """
        doc = self._get_document_by_id(doc_id)
        if doc.type == DocumentType.xliff:
            if not doc.xliff:
                raise EntityNotFound("No XLIFF file found")

            original_document = doc.xliff.original_document.encode("utf-8")
            processed_document = extract_xliff_content(original_document)

            for segment in processed_document.segments:
                record = (
                    self.__db.query(XliffRecord)
                    .filter_by(segment_id=segment.id_)
                    .first()
                )
                if record and not segment.approved:
                    segment.translation = record.parent.target
                    segment.approved = record.parent.approved
                    segment.state = SegmentState(record.state)

            processed_document.commit()
            file = processed_document.write()
            return StreamingResponse(
                file,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f'attachment; filename="{self.encode_to_latin_1(doc.name)}"'
                },
            )
        if doc.type == DocumentType.txt:
            if not doc.txt:
                raise EntityNotFound("No TXT file found")

            original_document = doc.txt.original_document
            processed_document = extract_txt_content(original_document)

            txt_records = doc.txt.records
            for i, segment in enumerate(processed_document.segments):
                record = txt_records[i]
                if record:
                    segment.translation = record.parent.target

            processed_document.commit()
            file = processed_document.write()
            return StreamingResponse(
                file,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f'attachment; filename="{self.encode_to_latin_1(doc.name)}"'
                },
            )

        raise EntityNotFound("Unknown document type")

    def get_document_records(
        self,
        doc_id: int,
        page: int,
        filters: doc_schema.DocumentRecordFilter | None = None,
    ) -> doc_schema.DocumentRecordListResponse:
        """
        Get records from a document.

        Args:
            doc_id: Document ID
            page: Page number
            filters: Optional filters for source/target text

        Returns:
            DocumentRecordListResponse object

        Raises:
            EntityNotFound: If document not found
        """
        doc = self._get_document_by_id(doc_id)
        total_records = self.__query.get_document_records_count_filtered(doc, filters)
        records = self.__query.get_document_records_paged(doc, page, filters=filters)

        record_list = [
            doc_schema.DocumentRecord(
                id=record.id,
                source=record.source,
                target=record.target,
                approved=record.approved,
                repetitions_count=repetitions_count,
                has_comments=has_comments,
            )
            for record, repetitions_count, has_comments in records
        ]

        return doc_schema.DocumentRecordListResponse(
            records=record_list,
            page=page,
            total_records=total_records,
        )

    @staticmethod
    def _are_segments_mergeable(
        old_history: DocumentRecordHistory,
        new_author: int | None,
        new_type: DocumentRecordHistoryChangeType,
    ):
        return (
            new_author is not None
            and old_history.author_id == new_author
            and old_history.change_type == new_type
        )

    def update_record(
        self,
        record_id: int,
        data: doc_schema.DocumentRecordUpdate,
        author_id: int,
        change_type: DocumentRecordHistoryChangeType,
        shallow: bool = False,
    ) -> doc_schema.DocumentRecordUpdateResponse:
        """
        Update a document record.

        Args:
            record_id: Record ID
            data: Updated record data
            author_id: Author ID of these changes
            change_type: Type of the change
            shallow: Whether to apply repetitions to its descendants

        Returns:
            DocumentRecordUpdateResponse object

        Raises:
            EntityNotFound: If record not found
        """
        try:
            record = self._get_record_by_id(record_id)
            old_target = record.target
            updated_record = self.__query.update_record(record_id, data)
            new_target = updated_record.target

            # TM tracking
            if data.approved and not shallow:
                for memory in record.document.memory_associations:
                    if memory.mode == TmMode.write:
                        self.__tm_query.add_or_update_record(
                            memory.tm_id, record.source, record.target
                        )
                        break

            self.track_history(
                record.id, old_target, new_target, author_id, change_type
            )

            # update repetitions
            if data.approved and data.update_repetitions and not shallow:
                updated_records = self.__query.get_record_ids_by_source(
                    record.document_id, record.source
                )

                for rec in updated_records:
                    # skip the current ID to avoid making more repetitions than needed
                    if rec == record.id:
                        continue

                    self.update_record(
                        rec,
                        data,
                        author_id,
                        DocumentRecordHistoryChangeType.repetition,
                        shallow=True,
                    )

            return doc_schema.DocumentRecordUpdateResponse.model_validate(
                updated_record
            )
        except NotFoundDocumentRecordExc:
            raise EntityNotFound("Record not found")

    def track_history(
        self,
        record_id: int,
        old_target: str,
        new_target: str,
        author_id: int,
        change_type: DocumentRecordHistoryChangeType,
    ):
        # Track history if the target changed
        if old_target == new_target:
            return

        last_history = self.__history_query.get_last_history_by_record_id(record_id)

        if last_history and DocumentService._are_segments_mergeable(
            last_history,
            author_id,
            change_type,
        ):
            # we need to reconstruct original string before doing a merge
            all_history = list(self.__history_query.get_history_by_record_id(record_id))

            diffs = [history.diff for history in all_history[1:]]
            original_text = reconstruct_from_diffs(reversed(diffs))
            merged_diff = compute_diff(original_text, new_target)

            self.__history_query.update_history_entry(
                last_history, merged_diff, datetime.now(UTC)
            )
        else:
            # diffs are not mergeable, create a new one
            self.__history_query.create_history_entry(
                record_id,
                compute_diff(old_target, new_target),
                author_id,
                change_type,
            )

    def get_segment_history(
        self, record_id: int
    ) -> doc_schema.DocumentRecordHistoryListResponse:
        """
        Get the history of changes for a document record.

        Args:
            record_id: Document record ID

        Returns:
            DocumentRecordHistoryResponse object

        Raises:
            EntityNotFound: If record not found
        """
        # Verify document record exists
        self._get_record_by_id(record_id)
        history_entries = self.__history_query.get_history_by_record_id(record_id)
        history_list = [
            doc_schema.DocumentRecordHistory(
                id=entry.id,
                diff=entry.diff,
                author=models.ShortUser.model_validate(entry.author)
                if entry.author
                else None,
                timestamp=entry.timestamp,
                change_type=entry.change_type,
            )
            for entry in history_entries
        ]

        return doc_schema.DocumentRecordHistoryListResponse(history=history_list)

    def get_glossaries(self, doc_id: int) -> list[doc_schema.DocGlossary]:
        """
        Get glossaries associated with a document.

        Args:
            doc_id: Document ID

        Returns:
            List of DocGlossary objects

        Raises:
            EntityNotFound: If document not found
        """
        doc = self._get_document_by_id(doc_id)
        return [
            doc_schema.DocGlossary(
                document_id=doc.id,
                glossary=GlossaryResponse.model_validate(x.glossary),
            )
            for x in doc.glossary_associations
        ]

    def set_glossaries(
        self, doc_id: int, settings: doc_schema.DocGlossaryUpdate
    ) -> models.StatusMessage:
        """
        Set glossaries for a document.

        Args:
            doc_id: Document ID
            settings: Glossary settings

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If document or glossary not found
        """
        doc = self._get_document_by_id(doc_id)
        glossary_ids = {g.id for g in settings.glossaries}
        try:
            if not glossary_ids:
                glossaries = []
            else:
                glossaries = list(self.__glossary_query.get_glossaries(list(glossary_ids)))
        except NotFoundGlossaryExc:
            raise EntityNotFound("Glossary not found")

        if len(glossary_ids) != len(glossaries):
            raise EntityNotFound("Not all glossaries were found")
        self.__query.set_document_glossaries(doc, glossaries)
        return models.StatusMessage(message="Glossary list updated")

    def get_translation_memories(
        self, doc_id: int
    ) -> list[doc_schema.DocTranslationMemory]:
        """
        Get translation memories associated with a document.

        Args:
            doc_id: Document ID

        Returns:
            List of DocTranslationMemory objects

        Raises:
            EntityNotFound: If document not found
        """
        doc = self._get_document_by_id(doc_id)
        return [
            doc_schema.DocTranslationMemory(
                document_id=doc.id,
                memory=TranslationMemory(
                    id=association.memory.id,
                    name=association.memory.name,
                    created_by=association.memory.created_by,
                ),
                mode=association.mode,
            )
            for association in self._get_document_by_id(doc_id).memory_associations
        ]

    def set_translation_memories(
        self, doc_id: int, settings: doc_schema.DocTranslationMemoryUpdate
    ) -> models.StatusMessage:
        """
        Set translation memories for a document.

        Args:
            doc_id: Document ID
            settings: Translation memory settings

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If document or memory not found, or invalid settings
        """
        # check writes count
        write_count = 0
        for memory in settings.memories:
            write_count += memory.mode == TmMode.write

        if write_count > 1:
            raise BusinessLogicError(
                "Only one translation memory can be set to write mode"
            )

        doc = self._get_document_by_id(doc_id)
        memory_ids = {memory.id for memory in settings.memories}
        memories = list(self.__tm_query.get_memories_by_id(memory_ids))
        if len(memory_ids) != len(memories):
            raise EntityNotFound("Not all memories were found")

        # Create list of (memory, mode) tuples
        memory_modes = []
        for setting in settings.memories:
            memory = next((m for m in memories if m.id == setting.id), None)
            if memory:
                memory_modes.append((memory, setting.mode))

        self.__query.set_document_memories(doc, memory_modes)
        return models.StatusMessage(message="Memory list updated")

    def search_tm_exact(
        self, doc_id: int, source: str
    ) -> TranslationMemoryListResponse:
        """
        Search translation memories for exact match.

        Args:
            doc_id: Document ID
            source: Source text to search for

        Returns:
            TranslationMemoryListResponse object

        Raises:
            EntityNotFound: If document not found
        """
        doc = self._get_document_by_id(doc_id)
        tm_ids = [tm.id for tm in doc.memories]

        if not tm_ids:
            return TranslationMemoryListResponse(records=[], page=0, total_records=0)

        records, count = self.__tm_query.get_memory_records_paged(
            memory_ids=tm_ids,
            page=0,
            page_records=20,
            query=source,
        )

        return TranslationMemoryListResponse(
            records=records,
            page=0,
            total_records=count,
        )

    def search_tm_similar(
        self, doc_id: int, source: str
    ) -> TranslationMemoryListSimilarResponse:
        """
        Search translation memories for similar matches.

        Args:
            doc_id: Document ID
            source: Source text to search for

        Returns:
            TranslationMemoryListSimilarResponse object

        Raises:
            EntityNotFound: If document not found
        """
        doc = self._get_document_by_id(doc_id)
        tm_ids = [tm.id for tm in doc.memories]

        if not tm_ids:
            return TranslationMemoryListSimilarResponse(
                records=[], page=0, total_records=0
            )

        records = self.__tm_query.get_memory_records_paged_similar(
            memory_ids=tm_ids,
            page_records=20,
            query=source,
        )

        return TranslationMemoryListSimilarResponse(
            records=records,
            page=0,
            total_records=len(records),
        )

    def get_comments(self, record_id: int) -> list[CommentResponse]:
        """
        Get all comments for a document record.

        Args:
            record_id: Document record ID

        Returns:
            List of CommentResponse objects

        Raises:
            EntityNotFound: If record not found
        """
        # Verify document record exists
        self._get_record_by_id(record_id)

        comments = self.__comments_query.get_comments_by_document_record(record_id)
        return [CommentResponse.model_validate(comment) for comment in comments]

    def create_comment(
        self, record_id: int, comment_data: CommentCreate, user_id: int
    ) -> CommentResponse:
        """
        Create a new comment for a document record.

        Args:
            record_id: Document record ID
            comment_data: Comment creation data
            user_id: ID of user creating the comment

        Returns:
            Created CommentResponse object

        Raises:
            EntityNotFound: If record not found
        """
        # Verify document record exists
        self._get_record_by_id(record_id)

        comment = self.__comments_query.create_comment(comment_data, user_id, record_id)
        return CommentResponse.model_validate(comment)

    def get_record_substitutions(self, record_id: int) -> list[MemorySubstitution]:
        """
        Get substitution suggestions for a document record.

        Args:
            record_id: Document record ID

        Returns:
            List of MemorySubstitution objects

        Raises:
            EntityNotFound: If record not found
        """
        original_segment = self._get_record_by_id(record_id)

        tm_ids = [tm.id for tm in original_segment.document.memories]
        return (
            self.__tm_query.get_substitutions(original_segment.source, tm_ids)
            if tm_ids
            else []
        )

    def get_record_glossary_records(self, record_id: int) -> list[GlossaryRecordSchema]:
        """
        Get glossary records matching a document record.

        Args:
            record_id: Document record ID

        Returns:
            List of GlossaryRecordSchema objects

        Raises:
            EntityNotFound: If record not found
        """
        original_segment = self._get_record_by_id(record_id)
        glossary_ids = [gl.id for gl in original_segment.document.glossaries]
        return (
            [
                GlossaryRecordSchema.model_validate(record)
                for record in self.__glossary_query.get_glossary_records_for_phrase(
                    original_segment.source, glossary_ids
                )
            ]
            if glossary_ids
            else []
        )

    def doc_glossary_search(
        self, doc_id: int, query: str
    ) -> list[GlossaryRecordSchema]:
        """
        Search glossaries for a phrase within a document.

        Args:
            doc_id: Document ID
            query: Search query

        Returns:
            List of GlossaryRecordSchema objects

        Raises:
            EntityNotFound: If document not found
        """
        doc = self._get_document_by_id(doc_id)
        glossary_ids = [gl.id for gl in doc.glossaries]

        return (
            [
                GlossaryRecordSchema.model_validate(record)
                for record in self.__glossary_query.get_glossary_records_for_phrase(
                    query, glossary_ids
                )
            ]
            if glossary_ids
            else []
        )

    def _get_document_by_id(self, doc_id: int) -> Document:
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document object

        Raises:
            EntityNotFound: If document not found
        """
        doc = self.__query.get_document(doc_id)
        if not doc:
            raise EntityNotFound("Document not found")
        return doc

    def _get_record_by_id(self, record_id: int):
        """
        Get a document record by ID.

        Args:
            record_id: Record ID

        Returns:
            DocumentRecord object

        Raises:
            EntityNotFound: If record not found
        """
        record = self.__query.get_record(record_id)
        if not record:
            raise EntityNotFound("Document record not found")
        return record

    def encode_to_latin_1(self, original: str):
        output = ""
        for c in original:
            output += c if (c.isalnum() or c in "'().[] -") else "_"
        return output

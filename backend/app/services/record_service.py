from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app import models
from app.base.exceptions import EntityNotFound
from app.comments.query import CommentsQuery
from app.comments.schema import CommentCreate, CommentResponse
from app.documents import schema as doc_schema
from app.documents.models import (
    DocumentRecordHistory,
    DocumentRecordHistoryChangeType,
    TmMode,
)
from app.documents.query import (
    DocumentRecordHistoryQuery,
    GenericDocsQuery,
)
from app.documents.utils import compute_diff, reconstruct_from_diffs
from app.glossary.query import GlossaryQuery
from app.glossary.schema import GlossaryRecordSchema
from app.records.query import NotFoundDocumentRecordExc, RecordsQuery
from app.translation_memory.query import TranslationMemoryQuery
from app.translation_memory.schema import MemorySubstitution


class RecordService:
    def __init__(self, db: Session):
        self.__query = RecordsQuery(db)
        self.__docs_query = GenericDocsQuery(db)
        self.__comments_query = CommentsQuery(db)
        self.__history_query = DocumentRecordHistoryQuery(db)
        self.__tm_query = TranslationMemoryQuery(db)
        self.__glossary_query = GlossaryQuery(db)

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
                updated_records = self.__docs_query.get_record_ids_by_source(
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

        if last_history and RecordService._are_segments_mergeable(
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

"""Document service for document and document record operations."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schema
from app.base.exceptions import BusinessLogicError, EntityNotFound
from app.documents import schema as doc_schema
from app.documents.models import (
    Document,
    DocumentType,
    TmMode,
    XliffRecord,
)
from app.documents.query import (
    GenericDocsQuery,
)
from app.formats.txt import extract_txt_content
from app.formats.xliff import SegmentState, extract_xliff_content
from app.glossary.query import GlossaryQuery, NotFoundGlossaryExc
from app.glossary.schema import GlossaryRecordSchema, GlossaryResponse
from app.projects.query import NotFoundProjectExc, ProjectQuery
from app.translation_memory.query import TranslationMemoryQuery
from app.translation_memory.schema import (
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
        self.__glossary_query = GlossaryQuery(db)
        self.__tm_query = TranslationMemoryQuery(db)

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
            project_id=doc.project_id,
            approved_records_count=records[0],
            total_records_count=records[1],
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
            project_id=None,
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

    def update_document(
        self, doc_id: int, update_data: doc_schema.DocumentUpdate, user_id: int
    ) -> doc_schema.DocumentUpdateResponse:
        """
        Update a document (name and/or project_id).

        Args:
            doc_id: Document ID
            update_data: DocumentUpdate object with optional name and project_id
            user_id: ID of user performing action

        Returns:
            DocumentUpdateResponse object

        Raises:
            EntityNotFound: If document or project not found
            UnauthorizedAccess: If user doesn't own project
        """
        self._get_document_by_id(doc_id)
        try:
            if update_data.project_id is not None and update_data.project_id != -1:
                pq = ProjectQuery(self.__db)
                # verify project exists
                pq._get_project(update_data.project_id)
        except NotFoundProjectExc:
            raise EntityNotFound("Project", update_data.project_id)

        updated_doc = self.__query.update_document(
            doc_id,
            update_data.name,
            update_data.project_id,
        )
        return doc_schema.DocumentUpdateResponse(
            id=updated_doc.id, name=updated_doc.name, project_id=updated_doc.project_id
        )

    def encode_to_latin_1(self, original: str):
        output = ""
        for c in original:
            output += c if (c.isalnum() or c in "'().[] -") else "_"
        return output

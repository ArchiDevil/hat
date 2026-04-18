"""Document service for document and document record operations."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO

from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schema
from app.base.exceptions import BusinessLogicError, EntityNotFound
from app.documents import schema as doc_schema
from app.documents.models import (
    Document,
    DocumentRecord,
    DocumentRecordHistoryChangeType,
    DocumentType,
    XliffRecord,
)
from app.documents.query import (
    DocumentRecordHistoryQuery,
    GenericDocsQuery,
)
from app.documents.utils import compute_diff
from app.formats.txt import extract_txt_content
from app.formats.xliff import (
    SegmentState,
    XliffNewFile,
    XliffSegment,
    extract_xliff_content,
)
from app.glossary.query import GlossaryQuery
from app.projects.query import NotFoundProjectExc, ProjectQuery
from app.translation_memory.query import TranslationMemoryQuery
from app.utils import encode_to_latin_1


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
        self.__history_query = DocumentRecordHistoryQuery(db)

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
        self, file: UploadFile, user_id: int, project_id: int
    ) -> doc_schema.Document:
        """
        Create a new document from uploaded file.

        Args:
            file: Uploaded file
            user_id: ID of user creating the document
            project_id: Optional ID of project to assign document to

        Returns:
            Created Document object

        Raises:
            EntityNotFound: If file type is unsupported or project not found
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

        # Validate project_id if provided
        try:
            pq = ProjectQuery(self.__db)
            pq._get_project(project_id)
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

        doc = Document(
            name=name,
            type=doc_type,
            processing_status=models.DocumentStatus.UPLOADED.value,
            upload_time=datetime.now(),
            created_by=user_id,
            project_id=project_id,
        )
        self.__query.add_document(doc, original_document)
        return doc_schema.Document(
            id=doc.id,
            name=doc.name,
            status=models.DocumentStatus(doc.processing_status),
            created_by=doc.created_by,
            type=doc.type.value,
            project_id=doc.project_id,
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
            document_id=doc_id,
            task_data=doc_schema.DocumentProcessingTaskData(
                task_type="document_processing",
                document_type=doc.type.value,
                settings=settings,
            ),
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
                    "Content-Disposition": f'attachment; filename="{encode_to_latin_1(doc.name)}"'
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
                    "Content-Disposition": f'attachment; filename="{encode_to_latin_1(doc.name)}"'
                },
            )

        raise EntityNotFound("Unknown document type")

    def download_original_document(self, doc_id: int) -> StreamingResponse:
        """
        Download original document.

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
            output = BytesIO(original_document)
        elif doc.type == DocumentType.txt:
            if not doc.txt:
                raise EntityNotFound("No TXT file found")
            original_document = doc.txt.original_document
            output = BytesIO(original_document.encode())
        else:
            raise EntityNotFound("Unknown document type")

        return StreamingResponse(
            output,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{encode_to_latin_1(doc.name)}"'
            },
        )

    def download_xliff(self, doc_id: int) -> StreamingResponse:
        """
        Download a document's XLIFF.

        Args:
            doc_id: Document ID

        Returns:
            StreamingResponse with XLIFF for a document

        Raises:
            EntityNotFound: If document not found or file not available
        """
        doc = self._get_document_by_id(doc_id)
        data = XliffNewFile(
            [
                XliffSegment(
                    id_=rec.id,
                    approved=rec.approved,
                    source=rec.source,
                    target=rec.target,
                    state=SegmentState.NEEDS_TRANSLATION.value
                    if not rec.approved
                    else SegmentState.FINAL.value,
                )
                for rec in doc.records
            ],
            str(doc.id),
        )
        file = data.serialize()
        return StreamingResponse(
            file,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{encode_to_latin_1(doc.name)}.xliff"'
            },
        )

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

        return doc_schema.DocumentRecordListResponse(
            records=[
                doc_schema.DocumentRecordExtended.model_validate(record)
                for record in records
            ],
            page=page,
            total_records=total_records,
        )

    def get_record_page(
        self,
        doc_id: int,
        record_id: int,
        filters: doc_schema.DocumentRecordFilter | None = None,
    ) -> doc_schema.RowPageResponse:
        doc = self._get_document_by_id(doc_id)
        page = self.__query.get_record_filtered_page(doc, record_id, filters)
        return doc_schema.RowPageResponse(page=page)

    def get_first_unapproved_record(
        self, doc_id: int
    ) -> doc_schema.DocumentRecord | None:
        doc = self._get_document_by_id(doc_id)
        record = self.__query.get_first_unapproved_record(doc)

        if not record:
            return None

        return doc_schema.DocumentRecord.model_validate(record)

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
            if update_data.project_id is not None:
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

    async def upload_xliff(
        self,
        file: UploadFile,
        options: doc_schema.XliffUploadOptions,
        current_user: int,
    ) -> models.StatusMessage:
        """
        Upload XLIFF file and update document records.

        Args:
            file: Uploaded XLIFF file
            options: Upload options including update_approved flag
            current_user: ID of user performing the upload

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If document not found
        """
        # Read file content
        file_data = await file.read()
        original_document = file_data.decode("utf-8")

        # Parse XLIFF
        try:
            xliff_data = extract_xliff_content(original_document.encode("utf-8"))
        except RuntimeError:
            raise BusinessLogicError("Invalid XLIFF format")

        # Extract document ID from first file element
        file_element = xliff_data.xliff_file.find(
            ".//{urn:oasis:names:tc:xliff:document:1.2}file",
            namespaces=xliff_data.xliff_file.nsmap,
        )
        if file_element is None:
            raise BusinessLogicError("Invalid XLIFF format: no file element found")

        doc_id_str = file_element.get("original")
        if not doc_id_str:
            raise BusinessLogicError(
                "Invalid XLIFF format: file element missing original attribute"
            )

        try:
            doc_id = int(doc_id_str)
        except ValueError:
            raise BusinessLogicError(f"Invalid document ID in XLIFF: {doc_id_str}")

        # Validate document exists
        self._get_document_by_id(doc_id)

        # Prepare history entries for bulk creation
        history_entries = []

        # Update records
        for segment in xliff_data.segments:
            record = (
                self.__db.query(DocumentRecord)
                .filter_by(document_id=doc_id, id=segment.id_)
                .first()
            )

            if not record:
                continue

            # Check if we should update this record
            should_update = options.update_approved or not record.approved

            if not should_update:
                continue

            old_target = record.target
            new_target = segment.translation or ""
            # Only update if the new translation is different and not empty
            if old_target != new_target and new_target:
                record.target = new_target
                record.approved = segment.approved

                # Prepare history entry
                history_entries.append(
                    (record.id, compute_diff(old_target, new_target))
                )

        # Bulk create history entries
        if history_entries:
            self.__history_query.bulk_create_history_entry(
                history_entries,
                current_user,
                DocumentRecordHistoryChangeType.translation_update,
            )

        self.__db.commit()
        updated_count = len(history_entries)
        return models.StatusMessage(
            message=f"Successfully updated {updated_count} record(s)"
        )

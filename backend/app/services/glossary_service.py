"""Glossary service for glossary and glossary record operations."""

import io
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self

import openpyxl
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app import Glossary, GlossaryRecord
from app.base.exceptions import EntityNotFound
from app.glossary.models import ProcessingStatuses
from app.glossary.query import (
    GlossaryQuery,
    NotFoundGlossaryExc,
    NotFoundGlossaryRecordExc,
)
from app.glossary.schema import (
    GlossaryRecordCreate,
    GlossaryRecordResponse,
    GlossaryRecordSchema,
    GlossaryRecordUpdate,
    GlossaryResponse,
    GlossarySchema,
)
from app.linguistic.utils import postprocess_stemmed_segment, stem_sentence
from app.models import StatusMessage


class GlossaryService:
    """Service for glossary and glossary record operations."""

    def __init__(self, db: Session):
        self.__query = GlossaryQuery(db)

    def list_glossaries(self) -> list[GlossaryResponse]:
        """
        Get list of all glossaries.

        Returns:
            List of GlossaryResponse objects
        """
        glossaries = self.__query.list_glossary()
        return [GlossaryResponse.model_validate(glossary) for glossary in glossaries]

    def get_glossary(self, glossary_id: int) -> GlossaryResponse:
        """
        Get a single glossary by ID.

        Args:
            glossary_id: Glossary ID

        Returns:
            GlossaryResponse object

        Raises:
            EntityNotFound: If glossary not found
        """
        try:
            doc = self.__query.get_glossary(glossary_id)
            return GlossaryResponse.model_validate(doc)
        except NotFoundGlossaryExc:
            raise EntityNotFound("Glossary", glossary_id)

    def create_glossary(
        self,
        data: GlossarySchema,
        user_id: int,
        processing_status: str = ProcessingStatuses.DONE,
    ) -> GlossaryResponse:
        """
        Create a new glossary.

        Args:
            data: Glossary schema data
            user_id: ID of user creating the glossary
            processing_status: Initial processing status

        Returns:
            Created GlossaryResponse object
        """
        glossary = self.__query.create_glossary(
            user_id=user_id, glossary=data, processing_status=processing_status
        )
        return GlossaryResponse.model_validate(glossary)

    def update_glossary(
        self, glossary_id: int, data: GlossarySchema
    ) -> GlossaryResponse:
        """
        Update a glossary.

        Args:
            glossary_id: Glossary ID
            data: Updated glossary schema data

        Returns:
            Updated GlossaryResponse object

        Raises:
            EntityNotFound: If glossary not found
        """
        try:
            glossary = self.__query.update_glossary(glossary_id, data)
            return GlossaryResponse.model_validate(glossary)
        except NotFoundGlossaryExc:
            raise EntityNotFound("Glossary", glossary_id)

    def delete_glossary(self, glossary_id: int) -> StatusMessage:
        """
        Delete a glossary.

        Args:
            glossary_id: Glossary ID

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If glossary not found
        """
        if not self.__query.delete_glossary(glossary_id):
            raise EntityNotFound("Glossary", glossary_id)
        return StatusMessage(message="Deleted")

    def list_glossary_records(
        self,
        glossary_id: int,
        page: int,
        page_records: int,
        search: str | None = None,
    ) -> GlossaryRecordResponse:
        """
        Get list of glossary records for a glossary.

        Args:
            glossary_id: Glossary ID
            page: Page number
            page_records: Number of records per page
            search: Optional search query

        Returns:
            GlossaryRecordResponse object with records and total count
        """
        try:
            self.__query.get_glossary(glossary_id)
        except NotFoundGlossaryExc:
            raise EntityNotFound("Glossary", glossary_id)
        records, total_rows = self.__query.list_glossary_records(
            glossary_id, page, page_records, search
        )
        return GlossaryRecordResponse(
            records=[GlossaryRecordSchema.model_validate(record) for record in records],
            total_rows=total_rows,
        )

    def create_glossary_record(
        self, glossary_id: int, data: GlossaryRecordCreate, user_id: int
    ) -> GlossaryRecordSchema:
        """
        Create a new glossary record.

        Args:
            glossary_id: Glossary ID
            data: Glossary record creation data
            user_id: ID of user creating the record

        Returns:
            Created GlossaryRecordSchema object

        Raises:
            EntityNotFound: If glossary not found
        """
        try:
            record = self.__query.create_glossary_record(
                user_id=user_id, glossary_id=glossary_id, record=data
            )
            return GlossaryRecordSchema.model_validate(record)
        except NotFoundGlossaryExc:
            raise EntityNotFound("Glossary not found")

    def update_glossary_record(
        self, record_id: int, data: GlossaryRecordUpdate
    ) -> GlossaryRecordSchema:
        """
        Update a glossary record.

        Args:
            record_id: Record ID
            data: Updated glossary record data

        Returns:
            Updated GlossaryRecordSchema object

        Raises:
            EntityNotFound: If record not found
        """
        try:
            record = self.__query.update_record(record_id, data)
            return GlossaryRecordSchema.model_validate(record)
        except NotFoundGlossaryRecordExc:
            raise EntityNotFound("Glossary record", record_id)

    def delete_glossary_record(self, record_id: int) -> StatusMessage:
        """
        Delete a glossary record.

        Args:
            record_id: Record ID

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If record not found
        """
        if not self.__query.delete_record(record_id):
            raise EntityNotFound("Glossary record", record_id)
        return StatusMessage(message="Deleted")

    def create_glossary_from_file(
        self, file: UploadFile, user_id: int, glossary_name: str
    ) -> tuple[object, Glossary]:
        """
        Create a glossary from an uploaded XLSX file.

        Args:
            file: Uploaded file
            user_id: ID of user creating the glossary
            glossary_name: Name for the glossary

        Returns:
            Tuple of (workbook sheet, created glossary)
        """
        content = file.file.read()
        xlsx = io.BytesIO(content)
        workbook = openpyxl.load_workbook(xlsx)
        sheet = workbook["Sheet1"]
        glossary_scheme = GlossarySchema(name=glossary_name)
        glossary_doc = self.__query.create_glossary(
            user_id=user_id, glossary=glossary_scheme
        )
        return sheet, glossary_doc

    def process_glossary_file(self, sheet, user_id: int, glossary_id: int) -> None:
        """
        Process glossary file and create records.

        Args:
            sheet: XLSX sheet object
            user_id: ID of user who uploaded the file
            glossary_id: Glossary ID to add records to
        """
        record_for_save = self._extract_from_xlsx(user_id, sheet, glossary_id)
        self.__query.bulk_create_glossary_record(record_for_save)
        self.__query.update_glossary_processing_status(glossary_id)

    def _extract_from_xlsx(
        self, user_id: int, sheet, glossary_id: int
    ) -> list[GlossaryRecord]:
        """
        Extract glossary records from XLSX sheet.

        Args:
            user_id: ID of user who uploaded the file
            sheet: XLSX sheet object
            glossary_id: Glossary ID to add records to

        Returns:
            List of GlossaryRecord objects
        """

        @dataclass
        class GlossaryRowRecord:
            comment: Optional[str]
            created_at: datetime
            author: str
            updated_at: datetime
            source: str
            target: str

            @classmethod
            def from_tuple(cls, data_tuple: tuple[str, ...]) -> Self:
                comment, created_at, author, updated_at, _, source, target = data_tuple
                created_at = datetime.strptime(created_at, "%m/%d/%Y %H:%M:%S")
                updated_at = datetime.strptime(updated_at, "%m/%d/%Y %H:%M:%S")
                return cls(comment, created_at, author, updated_at, source, target)

        record_for_save = []
        for cells in sheet.iter_rows(min_row=2, values_only=True):
            parsed_record = GlossaryRowRecord.from_tuple(cells)
            record = GlossaryRecord(
                created_by=user_id,
                created_at=parsed_record.created_at,
                updated_at=parsed_record.updated_at,
                comment=parsed_record.comment,
                source=parsed_record.source,
                target=parsed_record.target,
                glossary_id=glossary_id,
                stemmed_source=" ".join(
                    postprocess_stemmed_segment(stem_sentence(parsed_record.source))
                ),
            )
            record_for_save.append(record)
        return record_for_save

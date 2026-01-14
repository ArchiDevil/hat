"""Translation Memory service for TM operations."""

import io
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound
from app.formats.tmx import TmxData, TmxSegment, extract_tmx_content
from app.models import StatusMessage
from app.translation_memory import models, schema
from app.translation_memory.query import TranslationMemoryQuery


@dataclass
class DownloadMemoryData:
    """Data for downloading a translation memory as TMX file."""

    content: io.BytesIO
    filename: str


class TranslationMemoryService:
    """Service for translation memory operations."""

    def __init__(self, db: Session):
        self.__query = TranslationMemoryQuery(db)

    def get_memories(self) -> list[schema.TranslationMemory]:
        """
        Get all translation memories.

        Returns:
            List of TranslationMemory objects
        """
        return [
            schema.TranslationMemory(
                id=doc.id, name=doc.name, created_by=doc.created_by
            )
            for doc in self.__query.get_memories()
        ]

    def get_memory(self, tm_id: int) -> schema.TranslationMemoryWithRecordsCount:
        """
        Get a translation memory by ID.

        Args:
            tm_id: Translation memory ID

        Returns:
            TranslationMemoryWithRecordsCount object

        Raises:
            EntityNotFound: If memory not found
        """
        doc = self._get_memory_by_id(tm_id)
        return schema.TranslationMemoryWithRecordsCount(
            id=doc.id,
            name=doc.name,
            created_by=doc.created_by,
            records_count=self.__query.get_memory_records_count(tm_id),
        )

    def create_memory(self, name: str, user_id: int) -> schema.TranslationMemory:
        """
        Create a new translation memory.

        Args:
            name: Name for the translation memory
            user_id: ID of user creating the memory

        Returns:
            Created TranslationMemory object
        """
        doc = self.__query.add_memory(name, user_id, [])
        return schema.TranslationMemory(
            id=doc.id, name=doc.name, created_by=doc.created_by
        )

    async def create_memory_from_file(
        self, filename: str | None, content: bytes, user_id: int
    ) -> schema.TranslationMemory:
        """
        Create a translation memory from an uploaded TMX file.

        Args:
            file: Uploaded file
            user_id: ID of user creating the memory

        Returns:
            Created TranslationMemory object
        """
        segments = extract_tmx_content(content)

        doc = self.__query.add_memory(
            filename or "",
            user_id,
            [
                models.TranslationMemoryRecord(
                    source=segment.original,
                    target=segment.translation,
                    creation_date=segment.creation_date,
                    change_date=segment.change_date,
                )
                for segment in segments
            ],
        )

        return schema.TranslationMemory(
            id=doc.id, name=doc.name, created_by=doc.created_by
        )

    def delete_memory(self, tm_id: int) -> StatusMessage:
        """
        Delete a translation memory.

        Args:
            tm_id: Translation memory ID

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If memory not found
        """
        memory = self._get_memory_by_id(tm_id)
        self.__query.delete_memory(memory)
        return StatusMessage(message="Deleted")

    def get_memory_records(
        self, tm_id: int, page: int, query_str: str | None
    ) -> schema.TranslationMemoryListResponse:
        """
        Get records from a translation memory.

        Args:
            tm_id: Translation memory ID
            page: Page number
            query_str: Optional search query

        Returns:
            TranslationMemoryListResponse object

        Raises:
            EntityNotFound: If memory not found
        """
        page_records = 100
        self._get_memory_by_id(tm_id)
        records, count = self.__query.get_memory_records_paged(
            tm_id, page, page_records, query_str
        )
        return schema.TranslationMemoryListResponse(
            records=records, page=page, total_records=count
        )

    def get_memory_records_similar(
        self, tm_id: int, query_str: str
    ) -> schema.TranslationMemoryListSimilarResponse:
        """
        Get similar records from a translation memory.

        Args:
            tm_id: Translation memory ID
            query_str: Search query

        Returns:
            TranslationMemoryListSimilarResponse object

        Raises:
            EntityNotFound: If memory not found
        """
        page_records = 20
        self._get_memory_by_id(tm_id)
        records = self.__query.get_memory_records_paged_similar(
            tm_id, page_records, query_str
        )
        return schema.TranslationMemoryListSimilarResponse(
            records=records, page=0, total_records=len(records)
        )

    def download_memory(self, tm_id: int) -> DownloadMemoryData:
        """
        Prepare translation memory data for download as TMX file.

        Args:
            tm_id: Translation memory ID

        Returns:
            DownloadMemoryData with content and filename

        Raises:
            EntityNotFound: If memory not found
        """
        memory = self._get_memory_by_id(tm_id)
        data = TmxData(
            [
                TmxSegment(
                    original=record.source,
                    translation=record.target,
                    creation_date=record.creation_date,
                    change_date=record.change_date,
                )
                for record in memory.records
            ]
        )
        return DownloadMemoryData(content=data.write(), filename=f"{tm_id}.tmx")

    def _get_memory_by_id(self, tm_id: int) -> models.TranslationMemory:
        """
        Get a translation memory by ID.

        Args:
            tm_id: Translation memory ID

        Returns:
            TranslationMemory object

        Raises:
            EntityNotFound: If memory not found
        """
        doc = self.__query.get_memory(tm_id)
        if not doc:
            raise EntityNotFound("Memory not found")
        return doc

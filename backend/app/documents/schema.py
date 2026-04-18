from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.documents.models import DocumentRecordHistoryChangeType, TmMode
from app.glossary.schema import GlossaryResponse
from app.models import DocumentStatus, Identified, MachineTranslationSettings, ShortUser
from app.translation_memory.schema import TranslationMemory


class DocumentRecordFilter(BaseModel):
    source_filter: Optional[str]
    target_filter: Optional[str]


class Document(Identified):
    name: str
    status: DocumentStatus
    created_by: int
    type: Literal["xliff", "txt"]
    project_id: int


class DocumentWithRecordsCount(Document):
    approved_records_count: int
    total_records_count: int
    approved_word_count: int
    total_word_count: int


class DocumentRecord(Identified):
    source: str
    target: str
    approved: bool

    model_config = ConfigDict(from_attributes=True)


class DocumentRecordExtended(DocumentRecord):
    repetitions_count: int
    has_comments: bool
    row_number: int

    model_config = ConfigDict(from_attributes=True)


class DocumentRecordListResponse(BaseModel):
    records: list[DocumentRecordExtended]
    page: int
    total_records: int


class RowPageResponse(BaseModel):
    page: int | None


class DocumentRecordUpdateResponse(Identified):
    source: str
    target: str
    approved: bool

    model_config = ConfigDict(from_attributes=True)


class DocumentRecordUpdate(BaseModel):
    target: str
    approved: Optional[bool]
    update_repetitions: bool


class DocumentProcessingSettings(BaseModel):
    machine_translation_settings: Optional[MachineTranslationSettings]
    similarity_threshold: float = Field(default=1.0, ge=0.0, le=1.0)


class DocumentProcessingTaskData(BaseModel):
    task_type: Literal["document_processing"]
    document_type: Literal["xliff", "txt"]
    settings: DocumentProcessingSettings


class DocumentTaskDescription(BaseModel):
    document_id: int
    task_data: DocumentProcessingTaskData


class DocTranslationMemory(BaseModel):
    document_id: int
    memory: TranslationMemory
    mode: TmMode


class TranslationMemoryWithMode(Identified):
    mode: TmMode


class DocTranslationMemoryUpdate(BaseModel):
    memories: list[TranslationMemoryWithMode]


class DocGlossary(BaseModel):
    document_id: int
    glossary: GlossaryResponse


class DocGlossaryUpdate(BaseModel):
    glossaries: list[Identified]


class DocumentRecordHistory(BaseModel):
    id: int
    diff: str
    author: ShortUser | None
    timestamp: datetime
    change_type: DocumentRecordHistoryChangeType


class DocumentRecordHistoryListResponse(BaseModel):
    history: list[DocumentRecordHistory]


class DocumentUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        description="New name for the document.",
        min_length=1,
        max_length=255,
    )
    project_id: int | None = Field(
        default=None,
        description="ID of project to assign document to.",
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentUpdateResponse(BaseModel):
    id: int
    name: str
    project_id: int

    model_config = ConfigDict(from_attributes=True)


class XliffUploadOptions(BaseModel):
    update_approved: bool = Field(
        default=False,
        description="If True, forcefully update approved records. If False (default), skip approved records.",
    )

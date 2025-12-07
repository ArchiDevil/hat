from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.documents.models import RecordSource, TmMode
from app.glossary.schema import GlossaryResponse
from app.models import DocumentStatus, Identified, MachineTranslationSettings
from app.translation_memory.schema import TranslationMemory


class DocumentRecordFilter(BaseModel):
    source_filter: Optional[str]
    target_filter: Optional[str]


class Document(Identified):
    name: str
    status: DocumentStatus
    created_by: int
    type: Literal["xliff", "txt"]


class DocumentWithRecordsCount(Document):
    approved_records_count: int
    records_count: int


class DocumentRecord(Identified):
    source: str
    target: str
    approved: bool
    repetitions_count: int
    has_comments: bool
    translation_src: RecordSource | None


class DocumentRecordListResponse(BaseModel):
    records: list[DocumentRecord]
    page: int
    total_records: int


class DocumentRecordUpdateResponse(Identified):
    source: str
    target: str
    approved: bool


class DocumentRecordUpdate(BaseModel):
    target: str
    approved: Optional[bool]
    update_repetitions: bool


class DocumentProcessingSettings(BaseModel):
    machine_translation_settings: Optional[MachineTranslationSettings]
    similarity_threshold: float = Field(default=1.0, ge=0.0, le=1.0)


class DocumentTaskDescription(BaseModel):
    type: Literal["xliff", "txt"]
    document_id: int
    settings: DocumentProcessingSettings


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

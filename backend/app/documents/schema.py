from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.documents.models import TmMode
from app.models import DocumentStatus, Identified, MachineTranslationSettings
from app.translation_memory.schema import TranslationMemory, TranslationMemoryUsage


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


class DocumentRecordUpdate(BaseModel):
    target: str
    approved: Optional[bool]


class DocumentProcessingSettings(BaseModel):
    substitute_numbers: bool
    machine_translation_settings: Optional[MachineTranslationSettings]
    memory_ids: list[int]
    memory_usage: TranslationMemoryUsage
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

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
    records_count: int


class DocumentRecord(Identified):
    source: str
    target: str


class DocumentRecordUpdate(BaseModel):
    target: str


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
    doc_id: int
    memory: TranslationMemory
    mode: TmMode

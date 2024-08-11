from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models import DocumentStatus, Identified, MachineTranslationSettings
from app.translation_memory.schema import TranslationMemoryUsage


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
    tm_ids: list[int]
    tm_usage: TranslationMemoryUsage
    similarity_threshold: float = Field(default=1.0, ge=0.0, le=1.0)


class DocumentTaskDescription(BaseModel):
    type: Literal["xliff", "txt"]
    document_id: int
    settings: DocumentProcessingSettings

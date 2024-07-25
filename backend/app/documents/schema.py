from typing import Optional

from pydantic import BaseModel, Field

from app.models import MachineTranslationSettings, TmxUsage
from app.models import DocumentStatus, Identified


class Document(Identified):
    name: str
    status: DocumentStatus
    created_by: int


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
    tmx_file_ids: list[int]
    tmx_usage: TmxUsage
    similarity_threshold: float = Field(default=1.0, ge=0.0, le=1.0)

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DocumentStatus(Enum):
    UPLOADED = "uploaded"
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"


class TmxUsage(Enum):
    NEWEST = "newest"
    OLDEST = "oldest"


class TmxFile(BaseModel):
    id: int
    name: str


class TmxFileRecord(BaseModel):
    id: int
    source: str
    target: str


class TmxFileWithRecords(TmxFile):
    records: list[TmxFileRecord]


class XliffFile(BaseModel):
    id: int
    name: str
    status: DocumentStatus


class XliffFileRecord(BaseModel):
    id: int
    segment_id: int
    source: str
    target: str


class XliffFileWithRecords(XliffFile):
    records: list[XliffFileRecord]


class MachineTranslationSettings(BaseModel):
    # Yandex only for now
    # source_language: str
    # target_language: str
    folder_id: str
    oauth_token: str


class XliffProcessingSettings(BaseModel):
    substitute_numbers: bool
    use_machine_translation: bool
    machine_translation_settings: Optional[MachineTranslationSettings]
    tmx_file_ids: list[int]
    tmx_usage: TmxUsage


class StatusMessage(BaseModel):
    message: str

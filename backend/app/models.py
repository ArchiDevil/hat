from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


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


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


class Identified(BaseModel):
    id: int


class TmxFile(Identified):
    name: str


class TmxFileRecord(Identified):
    source: str
    target: str


class TmxFileWithRecords(TmxFile):
    records: list[TmxFileRecord]


class XliffFile(Identified):
    name: str
    status: DocumentStatus


class XliffFileRecord(Identified):
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


class UserFields(BaseModel):
    username: str
    email: str = Field(pattern=r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    role: UserRole
    disabled: bool


class UserToCreate(UserFields):
    password: str


class User(Identified, UserFields):
    pass


class AuthFields(BaseModel):
    email: str = Field(pattern=r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    password: str

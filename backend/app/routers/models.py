from enum import Enum
from pydantic import BaseModel


class DocumentStatus(Enum):
    UPLOADED = "uploaded"
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


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


class StatusMessage(BaseModel):
    message: str

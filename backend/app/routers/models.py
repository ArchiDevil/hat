from pydantic import BaseModel


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


class XliffFileRecord(BaseModel):
    id: int
    segment_id: int
    source: str
    target: str


class XliffFileWithRecords(XliffFile):
    records: list[XliffFileRecord]


class StatusMessage(BaseModel):
    message: str
